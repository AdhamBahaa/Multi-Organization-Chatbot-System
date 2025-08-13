"""
Pydantic models for the RAG Chatbot Backend
"""
from pydantic import BaseModel
from typing import Optional, List

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    username: str
    role: str

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
