"""
Pydantic models for the RAG Chatbot Backend
"""
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime

# Authentication Models
class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    email: str
    full_name: str
    role: str  # System role: super_admin, admin, user
    organization_role: Optional[str] = None  # Organization-specific role: Student, Teacher, etc.
    organization_id: int
    admin_id: Optional[int] = None

# Organization Models
class OrganizationCreate(BaseModel):
    name: str

class OrganizationUpdate(BaseModel):
    name: str

class OrganizationResponse(BaseModel):
    organization_id: int
    name: str
    created_at: datetime

    class Config:
        from_attributes = True

# Admin Models
class AdminCreate(BaseModel):
    organization_id: int
    full_name: str
    email: EmailStr

class AdminUpdate(BaseModel):
    full_name: str
    email: EmailStr

class AdminResponse(BaseModel):
    admin_id: int
    organization_id: int
    full_name: str
    email: str
    is_activated: bool
    created_at: datetime
    setup_link: Optional[str] = None

    class Config:
        from_attributes = True

# User Models
class UserCreate(BaseModel):
    admin_id: int
    full_name: str
    email: EmailStr
    role: str = "Member"  # Default to 'Member' to match database

class UserUpdate(BaseModel):
    full_name: str
    email: EmailStr
    role: str

class UserResponse(BaseModel):
    user_id: int
    admin_id: int
    organization_id: int
    full_name: str
    email: str
    role: str
    is_activated: bool
    created_at: datetime
    setup_link: Optional[str] = None

    class Config:
        from_attributes = True

# Password Management Models
class SetPasswordRequest(BaseModel):
    email: str
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        from .utils import validate_password_strength
        is_valid, error_message = validate_password_strength(v)
        if not is_valid:
            raise ValueError(error_message)
        return v

class UpdateProfileRequest(BaseModel):
    full_name: str
    email: EmailStr

# Chat Models
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[int] = None

class ChatResponse(BaseModel):
    response: str
    session_id: int
    message_id: int
    sources: List[dict] = []
    confidence: float = 0.0
    chunks_found: int = 0

# System Models
class SystemStatsResponse(BaseModel):
    total_documents: int
    total_chunks: int
    vector_db_status: str
    ai_configured: bool

class DocumentResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_type: str
    file_size: int
    file_path: str
    processed: bool
    chunk_count: int
    content_preview: str
    uploaded_at: float
