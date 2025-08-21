"""
Admin management routes (Super Admin only)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db, Organization, Admin
from ..models import AdminCreate, AdminUpdate, AdminResponse
from ..auth import get_current_super_admin
from ..email_service import email_service

router = APIRouter(prefix="/admins", tags=["Admins"])

@router.post("", response_model=AdminResponse)
async def create_admin(
    admin_data: AdminCreate,
    current_user = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    """Create a new admin (Super Admin only)"""
    
    # Check if organization exists
    organization = db.query(Organization).filter(
        Organization.OrganizationID == admin_data.organization_id
    ).first()
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Check if email already exists
    existing_email = db.query(Admin).filter(Admin.Email == admin_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create admin without password (will be set by admin later)
    admin = Admin(
        OrganizationID=admin_data.organization_id,
        FullName=admin_data.full_name,
        Email=admin_data.email,
        PasswordHash=None,  # No password initially
        isActivated=0  # Explicitly set to 0 (False) initially
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    
    # Generate setup link for the new admin
    setup_link = f"/setup-password?email={admin.Email}"
    
    # Send setup email to the new admin
    try:
        email_sent = email_service.send_setup_email(
            to_email=admin.Email,
            full_name=admin.FullName,
            setup_link=setup_link,
            role="admin"
        )
        if email_sent:
            print(f"✅ Setup email sent to admin: {admin.Email}")
        else:
            print(f"⚠️ Failed to send setup email to admin: {admin.Email}")
    except Exception as e:
        print(f"❌ Error sending setup email to admin {admin.Email}: {e}")
    
    return AdminResponse(
        admin_id=admin.AdminID,
        organization_id=admin.OrganizationID,
        full_name=admin.FullName,
        email=admin.Email,
        is_activated=admin.is_activated_bool,
        created_at=admin.CreatedAt,
        setup_link=setup_link
    )

@router.get("", response_model=List[AdminResponse])
async def list_admins(
    current_user = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    """List all admins (Super Admin only)"""
    admins = db.query(Admin).all()
    return [
        AdminResponse(
            admin_id=admin.AdminID,
            organization_id=admin.OrganizationID,
            full_name=admin.FullName,
            email=admin.Email,
            is_activated=admin.is_activated_bool,
            created_at=admin.CreatedAt
        )
        for admin in admins
    ]

@router.get("/{admin_id}", response_model=AdminResponse)
async def get_admin(
    admin_id: int,
    current_user = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    """Get admin details (Super Admin only)"""
    admin = db.query(Admin).filter(Admin.AdminID == admin_id).first()
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )
    
    return AdminResponse(
        admin_id=admin.AdminID,
        organization_id=admin.OrganizationID,
        full_name=admin.FullName,
        email=admin.Email,
        is_activated=admin.is_activated_bool,
        created_at=admin.CreatedAt
    )

@router.put("/{admin_id}", response_model=AdminResponse)
async def update_admin(
    admin_id: int,
    admin_data: AdminUpdate,
    current_user = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    """Update admin (Super Admin only)"""
    admin = db.query(Admin).filter(Admin.AdminID == admin_id).first()
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )
    
    # Check if email is already taken by another admin
    existing_email = db.query(Admin).filter(
        Admin.Email == admin_data.email,
        Admin.AdminID != admin_id
    ).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already taken by another admin"
        )
    
    admin.FullName = admin_data.full_name
    admin.Email = admin_data.email
    db.commit()
    db.refresh(admin)
    
    return AdminResponse(
        admin_id=admin.AdminID,
        organization_id=admin.OrganizationID,
        full_name=admin.FullName,
        email=admin.Email,
        is_activated=admin.is_activated_bool,
        created_at=admin.CreatedAt
    )

@router.delete("/{admin_id}")
async def delete_admin(
    admin_id: int,
    current_user = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    """Delete admin (Super Admin only) - This will also delete all users under this admin"""
    admin = db.query(Admin).filter(Admin.AdminID == admin_id).first()
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )
    
    # Delete admin (cascade will handle users)
    db.delete(admin)
    db.commit()
    
    return {"message": f"Admin '{admin.FullName}' deleted successfully"}
