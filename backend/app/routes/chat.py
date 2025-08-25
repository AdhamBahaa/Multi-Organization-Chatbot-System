"""
Chat routes for the RAG Chatbot Backend
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Union
from ..database import get_db, Admin, User, ChatSession, ChatMessage
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
        
        # Save chat messages to database (only for users, not admins)
        if isinstance(current_user, User):
            await save_chat_messages(db, current_user, chat_data, response)
        
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chat error: {str(e)}"
        )

async def save_chat_messages(db: Session, user: User, chat_data: ChatRequest, response: ChatResponse):
    """Save user message and bot response to database"""
    try:
        from sqlalchemy.sql import func
        
        # Get or create chat session
        if chat_data.session_id:
            session = db.query(ChatSession).filter(
                ChatSession.SessionID == chat_data.session_id,
                ChatSession.UserID == user.UserID
            ).first()
        else:
            # Create new session
            session = ChatSession(
                UserID=user.UserID,
                OrganizationID=user.OrganizationID,
                Title=chat_data.message[:50] + "..." if len(chat_data.message) > 50 else chat_data.message,
                IsActive=True
            )
            db.add(session)
            db.flush()  # Get the session ID
        
        # Get next message order
        max_order = db.query(ChatMessage).filter(
            ChatMessage.SessionID == session.SessionID
        ).with_entities(ChatMessage.MessageOrder).order_by(
            ChatMessage.MessageOrder.desc()
        ).first()
        
        next_order = (max_order[0] if max_order else 0) + 1
        
        # Save user message
        user_message = ChatMessage(
            SessionID=session.SessionID,
            UserID=user.UserID,
            Role="user",
            Content=chat_data.message,
            MessageOrder=next_order
        )
        db.add(user_message)
        
        # Save bot response
        bot_message = ChatMessage(
            SessionID=session.SessionID,
            UserID=user.UserID,
            Role="assistant",
            Content=response.response,
            MessageOrder=next_order + 1
        )
        db.add(bot_message)
        
        # Update session timestamp
        session.UpdatedAt = func.getdate()
        
        db.commit()
        
        # Update response with actual session ID
        response.session_id = session.SessionID
        
    except Exception as e:
        db.rollback()
        print(f"Error saving chat messages: {e}")
        # Don't fail the chat request if saving fails
