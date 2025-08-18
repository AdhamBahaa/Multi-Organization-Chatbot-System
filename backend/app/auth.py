"""
Authentication and authorization module for the RAG Chatbot Backend
"""
from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .database import get_db, Admin, User, Organization
from .models import TokenResponse

import secrets

# Generate a cryptographically secure random key
SECRET_KEY = secrets.token_urlsafe(32)
# Result: something like: "abc123def456ghi789jkl012mno345pqr678stu901vwx234yz"

# Security configuration
# SECRET_KEY = "your-secret-key-here"  # Change this in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token bearer
security = HTTPBearer()

# Super Admin configuration (only one exists)
SUPER_ADMIN_EMAIL = "superadmin@system.com"
SUPER_ADMIN_PASSWORD = "superadmin123"  # Change this in production

class AuthManager:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Generate password hash"""
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> dict:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    @staticmethod
    def authenticate_super_admin(email: str, password: str) -> bool:
        """Authenticate super admin"""
        return email == SUPER_ADMIN_EMAIL and password == SUPER_ADMIN_PASSWORD
    
    @staticmethod
    def authenticate_admin(db: Session, email: str, password: str) -> Optional[Admin]:
        """Authenticate admin user"""
        admin = db.query(Admin).filter(Admin.Email == email).first()
        if admin and admin.PasswordHash and AuthManager.verify_password(password, admin.PasswordHash):
            return admin
        return None
    
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate regular user"""
        user = db.query(User).filter(User.Email == email).first()
        if user and user.PasswordHash and AuthManager.verify_password(password, user.PasswordHash):
            return user
        return None

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Union[Admin, User]:
    """Get current authenticated user from token"""
    try:
        token = credentials.credentials
        payload = AuthManager.verify_token(token)
        
        user_id = payload.get("sub")  # Changed from "user_id" to "sub"
        role = payload.get("role")
        
        if role == "super_admin":
            # Create a Super Admin object for authentication
            super_admin = Admin(
                AdminID=0,
                OrganizationID=0,
                FullName="Super Admin",
                Email=payload.get("email", "superadmin@system.com"),
                PasswordHash="",
                CreatedAt=None
            )
            return super_admin
        elif role == "admin":
            user = db.query(Admin).filter(Admin.AdminID == user_id).first()
        elif role == "user":
            user = db.query(User).filter(User.UserID == user_id).first()
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user role"
            )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return user
        
    except Exception as e:
        raise

def get_current_admin(
    current_user: Union[Admin, User] = Depends(get_current_user)
) -> Admin:
    """Get current admin user (excludes Super Admin)"""
    if not isinstance(current_user, Admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Exclude Super Admin (AdminID = 0 indicates Super Admin)
    if current_user.AdminID == 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super Admin cannot access admin-only endpoints"
        )
    
    return current_user

def get_current_super_admin(
    current_user: Union[Admin, User] = Depends(get_current_user)
) -> Admin:
    """Get current super admin user"""
    # Check if this is a Super Admin (AdminID = 0 indicates Super Admin)
    if not isinstance(current_user, Admin) or current_user.AdminID != 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required"
        )
    
    return current_user

def create_user_token(user: Union[Admin, User], role: str) -> TokenResponse:
    """Create token response for user"""
    
    if isinstance(user, Admin):
        user_id = user.AdminID
        admin_id = None
        organization_id = user.OrganizationID
        organization_role = None  # Admins don't have organization-specific roles
    else:
        user_id = user.UserID
        admin_id = user.AdminID
        organization_id = user.OrganizationID
        organization_role = user.Role  # Get the organization-specific role
    
    token_data = {
        "sub": str(user_id),
        "role": role,
        "email": user.Email,
        "organization_id": organization_id,
        "admin_id": admin_id
    }
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = AuthManager.create_access_token(
        data=token_data,
        expires_delta=access_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user_id,
        email=user.Email,
        full_name=user.FullName,
        role=role,
        organization_role=organization_role,
        organization_id=organization_id,
        admin_id=admin_id
    )
