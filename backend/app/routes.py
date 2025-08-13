"""
API routes for the RAG Chatbot Backend
"""
from fastapi import APIRouter, Depends, UploadFile, File
from .models import LoginRequest, ChatRequest
from .auth import authenticate_user, get_current_user_info
from .chat import generate_chat_response, get_user_sessions
from .documents import get_all_documents, upload_document, delete_document, get_system_stats

# Create router
router = APIRouter(prefix="/api", tags=["API"])

# Authentication endpoints
@router.post("/login")
async def login(login_data: LoginRequest):
    """Login endpoint"""
    return await authenticate_user(login_data)

@router.get("/me")
async def get_current_user():
    """Get current user information"""
    return await get_current_user_info()

# Chat endpoints
@router.post("/chat")
async def chat(chat_data: ChatRequest):
    """Send a message and get AI-powered response with RAG"""
    return await generate_chat_response(chat_data)

@router.get("/sessions")
async def get_sessions():
    """Get user's chat sessions"""
    return await get_user_sessions()

# Document endpoints
@router.get("/documents")
async def get_documents():
    """Get all uploaded documents"""
    return await get_all_documents()

@router.post("/documents/upload")
async def upload_doc(file: UploadFile = File(...)):
    """Upload document endpoint"""
    return await upload_document(file)

@router.delete("/documents/{document_id}")
async def delete_doc(document_id: str):
    """Delete a document"""
    return await delete_document(document_id)

# System endpoints
@router.get("/system/stats")
async def get_stats():
    """Get system statistics"""
    return await get_system_stats()

# Health endpoints
@router.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "RAG Chatbot API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "login": "/api/login",
            "chat": "/api/chat",
            "documents": "/api/documents"
        }
    }

@router.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "version": "1.0.0"
    }
