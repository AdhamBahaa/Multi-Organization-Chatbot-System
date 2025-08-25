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
    role: str
    organization_role: Optional[str] = None
    organization_id: int
    admin_id: Optional[int] = None

class UserInfo(BaseModel):
    user_id: int
    admin_id: int
    organization_id: int
    full_name: str
    email: str
    role: str
    is_activated: bool
    user_type: str  # "admin" or "user"

    class Config:
        from_attributes = True

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
    role: str = "Member"

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

# Document Models
class DocumentUploadResponse(BaseModel):
    message: str
    document_id: str
    filename: str
    chunks_created: int

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

# Chat History Models
class ChatSessionResponse(BaseModel):
    session_id: int
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int
    is_active: bool

    class Config:
        from_attributes = True

class ChatMessageResponse(BaseModel):
    message_id: int
    session_id: int
    role: str
    content: str
    timestamp: datetime
    message_order: int

    class Config:
        from_attributes = True

class ChatHistoryResponse(BaseModel):
    session: ChatSessionResponse
    messages: List[ChatMessageResponse]

# Feedback Models
class FeedbackCreate(BaseModel):
    session_id: int
    message_id: int
    user_message: str
    bot_response: str
    rating: int
    comment: Optional[str] = None
    
    @validator('session_id', 'message_id', 'rating', pre=True)
    def convert_to_int(cls, v):
        if isinstance(v, str):
            return int(v)
        return v
    
    @validator('rating')
    def validate_rating(cls, v):
        if v < 1 or v > 5:
            raise ValueError('Rating must be between 1 and 5')
        return v

class FeedbackResponse(BaseModel):
    feedback_id: int
    user_id: int
    organization_id: int
    session_id: int
    message_id: int
    user_message: str
    bot_response: str
    rating: int
    comment: Optional[str]
    created_at: datetime
    user_name: str
    user_role: str

    class Config:
        from_attributes = True

# System Models
class SystemStatsResponse(BaseModel):
    total_documents: int
    total_chunks: int
    vector_db_status: str
    ai_configured: bool

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

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        from .utils import validate_password_strength
        is_valid, error_message = validate_password_strength(v)
        if not is_valid:
            raise ValueError(error_message)
        return v
