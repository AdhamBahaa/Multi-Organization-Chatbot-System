"""
Organization management routes (Super Admin only)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db, Organization
from ..models import OrganizationCreate, OrganizationUpdate, OrganizationResponse
from ..auth import get_current_super_admin

router = APIRouter(prefix="/organizations", tags=["Organizations"])

@router.post("", response_model=OrganizationResponse)
async def create_organization(
    org_data: OrganizationCreate,
    current_user = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    """Create a new organization (Super Admin only)"""
    
    # Check if organization name already exists
    existing_org = db.query(Organization).filter(
        Organization.Name == org_data.name
    ).first()
    if existing_org:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization name already exists"
        )
    
    # Create organization
    organization = Organization(Name=org_data.name)
    db.add(organization)
    db.commit()
    db.refresh(organization)
    
    return OrganizationResponse(
        organization_id=organization.OrganizationID,
        name=organization.Name,
        created_at=organization.CreatedAt
    )

@router.get("", response_model=List[OrganizationResponse])
async def list_organizations(
    current_user = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    """List all organizations (Super Admin only)"""
    organizations = db.query(Organization).all()
    
    return [
        OrganizationResponse(
            organization_id=org.OrganizationID,
            name=org.Name,
            created_at=org.CreatedAt
        )
        for org in organizations
    ]

@router.get("/{organization_id}", response_model=OrganizationResponse)
async def get_organization(
    organization_id: int,
    current_user = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    """Get organization details (Super Admin only)"""
    organization = db.query(Organization).filter(
        Organization.OrganizationID == organization_id
    ).first()
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    return OrganizationResponse(
        organization_id=organization.OrganizationID,
        name=organization.Name,
        created_at=organization.CreatedAt
    )

@router.put("/{organization_id}", response_model=OrganizationResponse)
async def update_organization(
    organization_id: int,
    org_data: OrganizationUpdate,
    current_user = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    """Update organization (Super Admin only)"""
    organization = db.query(Organization).filter(
        Organization.OrganizationID == organization_id
    ).first()
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Check if new name conflicts with existing organization
    existing_org = db.query(Organization).filter(
        Organization.Name == org_data.name,
        Organization.OrganizationID != organization_id
    ).first()
    if existing_org:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization name already exists"
        )
    
    organization.Name = org_data.name
    db.commit()
    db.refresh(organization)
    
    return OrganizationResponse(
        organization_id=organization.OrganizationID,
        name=organization.Name,
        created_at=organization.CreatedAt
    )

@router.delete("/{organization_id}")
async def delete_organization(
    organization_id: int,
    current_user = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    """Delete organization (Super Admin only) - This will also delete all admins and users"""
    organization = db.query(Organization).filter(
        Organization.OrganizationID == organization_id
    ).first()
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Delete organization (cascade will handle admins and users)
    db.delete(organization)
    db.commit()
    
    return {"message": f"Organization '{organization.Name}' deleted successfully"}
