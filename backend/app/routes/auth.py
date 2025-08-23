"""
Authentication and user management routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Union
from pydantic import BaseModel, validator
from ..database import get_db, Admin, User
from ..models import LoginRequest, TokenResponse, SetPasswordRequest, UpdateProfileRequest
from ..auth import AuthManager, get_current_user, create_user_token
from ..email_service import email_service

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=TokenResponse)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """User login endpoint"""
    
    # Try to authenticate as Super Admin first
    if AuthManager.authenticate_super_admin(login_data.email, login_data.password):
        # Create token for Super Admin
        super_admin_obj = Admin(
            AdminID=0,
            OrganizationID=0,
            FullName="Super Admin",
            Email=login_data.email,
            PasswordHash="",
            CreatedAt=None
        )
        
        token_response = create_user_token(super_admin_obj, "super_admin")
        return token_response
    
    # Check if admin exists but has no password (first-time setup)
    admin = db.query(Admin).filter(Admin.Email == login_data.email).first()
    if admin and admin.PasswordHash is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Password not set. Please use the setup link to set your password."
        )
    
    # Try to authenticate as Admin
    admin = AuthManager.authenticate_admin(db, login_data.email, login_data.password)
    if admin:
        return create_user_token(admin, "admin")
    
    # Check if user exists but has no password (first-time setup)
    user = db.query(User).filter(User.Email == login_data.email).first()
    if user and user.PasswordHash is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Password not set. Please use the setup link to set your password."
        )
    
    # Try to authenticate as User
    user = AuthManager.authenticate_user(db, login_data.email, login_data.password)
    if user:
        return create_user_token(user, "user")  # System role is always "user" for regular users
    
    # Authentication failed
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password"
    )

@router.post("/set-password")
async def set_password(
    password_data: SetPasswordRequest,
    db: Session = Depends(get_db)
):
    """Set password for admin or user (first-time setup)"""
    
    # Check if admin exists
    admin = db.query(Admin).filter(Admin.Email == password_data.email).first()
    if admin:
        if admin.PasswordHash is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password already set for this admin"
            )
        
        # Set password for admin and mark as activated
        admin.PasswordHash = AuthManager.get_password_hash(password_data.password)
        admin.isActivated = 1  # Use integer 1 for True
        db.commit()
        db.refresh(admin)  # Refresh the object to get updated values
        

        
        # Send welcome email to admin
        try:
            email_service.send_welcome_email(
                to_email=admin.Email,
                full_name=admin.FullName,
                role="admin"
            )
        except Exception as e:
            print(f"❌ Error sending welcome email to admin {admin.Email}: {e}")
        
        return {"message": "Admin password set successfully"}
    
    # Check if user exists
    user = db.query(User).filter(User.Email == password_data.email).first()
    if user:
        if user.PasswordHash is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password already set for this user"
            )
        
        # Set password for user and mark as activated
        user.PasswordHash = AuthManager.get_password_hash(password_data.password)
        user.isActivated = 1  # Use integer 1 for True
        db.commit()
        db.refresh(user)  # Refresh the object to get updated values
        
        # Send welcome email to user
        try:
            email_service.send_welcome_email(
                to_email=user.Email,
                full_name=user.FullName,
                role="user"
            )
        except Exception as e:
            print(f"❌ Error sending welcome email to user {user.Email}: {e}")
        
        return {"message": "User password set successfully"}
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Email not found"
    )

@router.put("/profile")
async def update_profile(
    profile_data: UpdateProfileRequest,
    current_user: Union[Admin, User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile (name and email)"""
    
    # Check if email is already taken by another user (cross-table validation)
    if isinstance(current_user, Admin):
        # Check if email exists in Admin table (excluding current admin)
        existing_admin = db.query(Admin).filter(
            Admin.Email == profile_data.email,
            Admin.AdminID != current_user.AdminID
        ).first()
        if existing_admin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already registered"
            )
        
        # Check if email exists in User table
        existing_user = db.query(User).filter(User.Email == profile_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already registered"
            )
    else:
        # Check if email exists in User table (excluding current user)
        existing_user = db.query(User).filter(
            User.Email == profile_data.email,
            User.UserID != current_user.UserID
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already registered"
            )
        
        # Check if email exists in Admin table
        existing_admin = db.query(Admin).filter(Admin.Email == profile_data.email).first()
        if existing_admin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already registered"
            )
    
    # Update profile
    current_user.FullName = profile_data.full_name
    current_user.Email = profile_data.email
    db.commit()
    
    return {"message": "Profile updated successfully"}

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        from ..utils import validate_password_strength
        is_valid, error_message = validate_password_strength(v)
        if not is_valid:
            raise ValueError(error_message)
        return v

@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: Union[Admin, User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change password for authenticated user"""
    
    # Verify current password
    if not AuthManager.verify_password(password_data.current_password, current_user.PasswordHash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    current_user.PasswordHash = AuthManager.get_password_hash(password_data.new_password)
    db.commit()
    
    # Send email notification
    try:
        from ..email_service import EmailService
        email_service = EmailService()
        
        # Determine role and send notification
        if isinstance(current_user, Admin):
            role = "admin"
            if current_user.AdminID == 0:
                role = "super_admin"
        else:
            role = "user"
        
        email_service.send_password_change_notification(
            to_email=current_user.Email,
            full_name=current_user.FullName,
            role=role
        )
    except Exception as e:
        print(f"⚠️ Failed to send password change notification: {e}")
        # Don't fail the password change if email fails
    
    return {"message": "Password changed successfully"}

@router.get("/profile")
async def get_user_profile(current_user: Union[Admin, User] = Depends(get_current_user)):
    """Get current user profile"""
    if isinstance(current_user, Admin):
        # Check if this is Super Admin (AdminID = 0)
        role = "super_admin" if current_user.AdminID == 0 else "admin"
        return {
            "user_id": current_user.AdminID,
            "email": current_user.Email,
            "full_name": current_user.FullName,
            "role": role,
            "organization_id": current_user.OrganizationID,
            "created_at": current_user.CreatedAt
        }
    else:
        return {
            "user_id": current_user.UserID,
            "email": current_user.Email,
            "full_name": current_user.FullName,
            "role": current_user.Role,
            "admin_id": current_user.AdminID,
            "organization_id": current_user.OrganizationID,
            "created_at": current_user.CreatedAt
        }

@router.get("/my-organization")
async def get_my_organization(
    current_user: Union[Admin, User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get organization information for the current user"""
    from ..database import Organization
    
    organization = db.query(Organization).filter(
        Organization.OrganizationID == current_user.OrganizationID
    ).first()
    
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    return {
        "organization_id": organization.OrganizationID,
        "name": organization.Name,
        "created_at": organization.CreatedAt
    }

@router.get("/my-admin")
async def get_my_admin(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get admin information for the current user"""
    from ..database import Admin
    
    admin = db.query(Admin).filter(
        Admin.AdminID == current_user.AdminID
    ).first()
    
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )
    
    return {
        "admin_id": admin.AdminID,
        "full_name": admin.FullName,
        "email": admin.Email,
        "created_at": admin.CreatedAt
    }

@router.post("/refresh-session")
async def refresh_session(
    current_user: Union[Admin, User] = Depends(get_current_user)
):
    """Refresh user session by extending token expiry"""
    try:
        # Determine role based on user type
        if isinstance(current_user, Admin):
            if current_user.AdminID == 0:
                role = "super_admin"
            else:
                role = "admin"
        else:
            role = "user"
        
        # Create new token with extended expiry
        token_response = create_user_token(current_user, role)
        
        return {
            "success": True,
            "access_token": token_response.access_token,
            "message": "Session refreshed successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh session"
        )

@router.post("/logout")
async def logout():
    """Logout endpoint (client-side token removal)"""
    return {"message": "Logged out successfully"}
