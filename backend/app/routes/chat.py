"""
Chat routes for the RAG Chatbot Backend
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Union
from ..database import get_db, Admin, User
from ..auth import get_current_user
from ..chat import generate_chat_response
from ..models import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("", response_model=ChatResponse)
async def chat_endpoint(
    chat_data: ChatRequest,
    current_user: Union[Admin, User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Chat endpoint for AI-powered responses with RAG functionality"""
    try:
        # Get organization ID from current user
        if isinstance(current_user, Admin):
            organization_id = current_user.OrganizationID
        else:  # User
            organization_id = current_user.OrganizationID
        
        response = await generate_chat_response(chat_data, organization_id)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chat error: {str(e)}"
        )
