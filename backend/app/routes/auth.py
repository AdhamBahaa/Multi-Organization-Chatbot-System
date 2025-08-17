"""
Authentication and user management routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Union
from ..database import get_db, Admin, User
from ..models import LoginRequest, TokenResponse, SetPasswordRequest, UpdateProfileRequest
from ..auth import AuthManager, get_current_user, create_user_token

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
    
    # Try to authenticate as Admin
    admin = AuthManager.authenticate_admin(db, login_data.email, login_data.password)
    if admin:
        return create_user_token(admin, "admin")
    
    # Try to authenticate as User
    user = AuthManager.authenticate_user(db, login_data.email, login_data.password)
    if user:
        return create_user_token(user, "user")
    
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
        
        # Set password for admin
        admin.PasswordHash = AuthManager.get_password_hash(password_data.password)
        db.commit()
        return {"message": "Admin password set successfully"}
    
    # Check if user exists
    user = db.query(User).filter(User.Email == password_data.email).first()
    if user:
        if user.PasswordHash is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password already set for this user"
            )
        
        # Set password for user
        user.PasswordHash = AuthManager.get_password_hash(password_data.password)
        db.commit()
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
    
    # Check if email is already taken by another user
    if isinstance(current_user, Admin):
        existing_email = db.query(Admin).filter(
            Admin.Email == profile_data.email,
            Admin.AdminID != current_user.AdminID
        ).first()
    else:
        existing_email = db.query(User).filter(
            User.Email == profile_data.email,
            User.UserID != current_user.UserID
        ).first()
    
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already taken by another user"
        )
    
    # Update profile
    current_user.FullName = profile_data.full_name
    current_user.Email = profile_data.email
    db.commit()
    
    return {"message": "Profile updated successfully"}

@router.post("/change-password")
async def change_password(
    current_password: str,
    new_password: str,
    current_user: Union[Admin, User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change password for authenticated user"""
    
    # Verify current password
    if not AuthManager.verify_password(current_password, current_user.PasswordHash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    current_user.PasswordHash = AuthManager.get_password_hash(new_password)
    db.commit()
    
    return {"message": "Password changed successfully"}

@router.get("/profile")
async def get_user_profile(current_user: Union[Admin, User] = Depends(get_current_user)):
    """Get current user profile"""
    if isinstance(current_user, Admin):
        return {
            "user_id": current_user.AdminID,
            "email": current_user.Email,
            "full_name": current_user.FullName,
            "role": "admin",
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
