"""
User management routes (Admin only)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db, Admin, User
from ..models import UserCreate, UserUpdate, UserResponse
from ..auth import get_current_admin

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Create a new user (Admin only)"""
    
    # Check if admin ID matches current admin
    if current_admin.AdminID != user_data.admin_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only create users under your own admin account"
        )
    
    # Check if email already exists
    existing_email = db.query(User).filter(User.Email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user without password (will be set by user later)
    # User automatically gets assigned to the Admin's organization
    user = User(
        AdminID=user_data.admin_id,
        OrganizationID=current_admin.OrganizationID,  # Use Admin's organization
        FullName=user_data.full_name,
        Email=user_data.email,
        PasswordHash=None,  # No password initially
        Role=user_data.role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return UserResponse(
        user_id=user.UserID,
        admin_id=user.AdminID,
        organization_id=user.OrganizationID,
        full_name=user.FullName,
        email=user.Email,
        role=user.Role,
        created_at=user.CreatedAt
    )

@router.get("", response_model=List[UserResponse])
async def list_organization_users(
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """List all users in the admin's organization"""
    users = db.query(User).filter(
        User.OrganizationID == current_admin.OrganizationID
    ).all()
    
    return [
        UserResponse(
            user_id=user.UserID,
            admin_id=user.AdminID,
            organization_id=user.OrganizationID,
            full_name=user.FullName,
            email=user.Email,
            role=user.Role,
            created_at=user.CreatedAt
        )
        for user in users
    ]

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get user details (Admin only - within their organization)"""
    user = db.query(User).filter(
        User.UserID == user_id,
        User.OrganizationID == current_admin.OrganizationID
    ).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in your organization"
        )
    
    return UserResponse(
        user_id=user.UserID,
        admin_id=user.AdminID,
        organization_id=user.OrganizationID,
        full_name=user.FullName,
        email=user.Email,
        role=user.Role,
        created_at=user.CreatedAt
    )

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update user (Admin only - within their organization)"""
    user = db.query(User).filter(
        User.UserID == user_id,
        User.OrganizationID == current_admin.OrganizationID
    ).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in your organization"
        )
    
    # Check if email is already taken by another user
    existing_email = db.query(User).filter(
        User.Email == user_data.email,
        User.UserID != user_id
    ).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already taken by another user"
        )
    
    user.FullName = user_data.full_name
    user.Email = user_data.email
    user.Role = user_data.role
    db.commit()
    db.refresh(user)
    
    return UserResponse(
        user_id=user.UserID,
        admin_id=user.AdminID,
        organization_id=user.OrganizationID,
        full_name=user.FullName,
        email=user.Email,
        role=user.Role,
        created_at=user.CreatedAt
    )

@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Delete user (Admin only - within their organization)"""
    user = db.query(User).filter(
        User.UserID == user_id,
        User.OrganizationID == current_admin.OrganizationID
    ).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in your organization"
        )
    
    # Delete user
    db.delete(user)
    db.commit()
    
    return {"message": f"User '{user.FullName}' deleted successfully"}
