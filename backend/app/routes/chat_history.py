"""
Chat History routes for the RAG Chatbot Backend
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Union
from ..database import get_db, ChatSession, ChatMessage, User, Admin
from ..models import ChatSessionResponse, ChatMessageResponse, ChatHistoryResponse
from ..auth import get_current_user

router = APIRouter()

@router.get("/sessions", response_model=List[ChatSessionResponse])
async def get_user_sessions(
    current_user: Union[Admin, User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all chat sessions for the current user"""
    
    # Only users can view their chat history
    if isinstance(current_user, Admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only users can view chat history"
        )
    
    # Get all sessions for the user, ordered by most recent
    sessions = db.query(ChatSession).filter(
        ChatSession.UserID == current_user.UserID
    ).order_by(ChatSession.UpdatedAt.desc()).all()
    
    # Convert to response models with message count
    session_responses = []
    for session in sessions:
        message_count = db.query(ChatMessage).filter(
            ChatMessage.SessionID == session.SessionID
        ).count()
        
        session_responses.append(ChatSessionResponse(
            session_id=session.SessionID,
            title=session.Title or "Untitled Conversation",
            created_at=session.CreatedAt,
            updated_at=session.UpdatedAt,
            message_count=message_count,
            is_active=session.IsActive
        ))
    
    return session_responses

@router.get("/sessions/{session_id}", response_model=ChatHistoryResponse)
async def get_session_history(
    session_id: int,
    current_user: Union[Admin, User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all messages for a specific chat session"""
    
    # Only users can view their chat history
    if isinstance(current_user, Admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only users can view chat history"
        )
    
    # Get the session and verify ownership
    session = db.query(ChatSession).filter(
        ChatSession.SessionID == session_id,
        ChatSession.UserID == current_user.UserID
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    # Get all messages for this session, ordered by message order
    messages = db.query(ChatMessage).filter(
        ChatMessage.SessionID == session_id
    ).order_by(ChatMessage.MessageOrder).all()
    
    # Convert to response models
    message_responses = [
        ChatMessageResponse(
            message_id=msg.MessageID,
            session_id=msg.SessionID,
            role=msg.Role,
            content=msg.Content,
            timestamp=msg.Timestamp,
            message_order=msg.MessageOrder
        )
        for msg in messages
    ]
    
    # Create session response
    session_response = ChatSessionResponse(
        session_id=session.SessionID,
        title=session.Title or "Untitled Conversation",
        created_at=session.CreatedAt,
        updated_at=session.UpdatedAt,
        message_count=len(messages),
        is_active=session.IsActive
    )
    
    return ChatHistoryResponse(
        session=session_response,
        messages=message_responses
    )

@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: int,
    current_user: Union[Admin, User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a chat session and all its messages"""
    
    # Only users can delete their own sessions
    if isinstance(current_user, Admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only users can delete their chat sessions"
        )
    
    # Get the session and verify ownership
    session = db.query(ChatSession).filter(
        ChatSession.SessionID == session_id,
        ChatSession.UserID == current_user.UserID
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    try:
        # Delete the session (messages will be deleted due to cascade)
        db.delete(session)
        db.commit()
        
        return {"message": "Chat session deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete chat session: {str(e)}"
        )
