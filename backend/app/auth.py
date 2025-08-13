"""
Authentication module for the RAG Chatbot Backend
"""
from fastapi import HTTPException, status
from .models import LoginRequest, TokenResponse
from .config import DEMO_USERS

async def authenticate_user(login_data: LoginRequest) -> TokenResponse:
    """Authenticate user and return token response"""
    user_data = DEMO_USERS.get(login_data.username)
    
    if not user_data or user_data["password"] != login_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Create mock token (in production, use proper JWT)
    access_token = f"mock-token-{user_data['username']}-{user_data['role']}"
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user_data["id"],
        username=user_data["username"],
        role=user_data["role"]
    )

async def get_current_user_info():
    """Get current user information (mock response)"""
    return {
        "id": 1,
        "username": "demo_user",
        "email": "demo@example.com",
        "role": "user",
        "is_active": True,
        "created_at": "2025-08-10T00:00:00"
    }
