"""
Feedback routes for the RAG Chatbot Backend
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Union
from ..database import get_db, Feedback, User, Admin
from ..models import FeedbackCreate, FeedbackResponse
from ..auth import get_current_user

router = APIRouter()

@router.post("/submit", response_model=dict)
async def submit_feedback(
    request: Request,
    current_user: Union[Admin, User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit feedback for a chatbot response"""
    
    # Debug: Print the raw request body
    try:
        body = await request.json()
        print(f"🔍 Raw request body: {body}")
        print(f"🔍 Body types: session_id={type(body.get('session_id'))}, message_id={type(body.get('message_id'))}, rating={type(body.get('rating'))}")
        print(f"🔍 User message (raw): {repr(body.get('user_message', ''))}")
        print(f"🔍 Bot response (raw): {repr(body.get('bot_response', ''))}")
    except Exception as e:
        print(f"🔍 Could not read raw body: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON: {str(e)}"
        )
    
    # Only users can submit feedback
    if isinstance(current_user, Admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only users can submit feedback"
        )
    
    # Manual validation and conversion
    try:
        session_id = int(body.get('session_id', 0))
        message_id = int(body.get('message_id', 0))
        user_message = str(body.get('user_message', ''))
        bot_response = str(body.get('bot_response', ''))
        rating = int(body.get('rating', 0))
        comment = body.get('comment')
        
        # Validate required fields
        if not user_message or not bot_response:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="user_message and bot_response are required"
            )
        
        # Validate rating
        if rating < 1 or rating > 5:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Rating must be between 1 and 5"
            )
        
        print(f"🔍 Validated data: session_id={session_id}, message_id={message_id}, rating={rating}")
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid data types: {str(e)}"
        )
    
    # Create new feedback record
    new_feedback = Feedback(
        UserID=current_user.UserID,
        OrganizationID=current_user.OrganizationID,
        SessionID=session_id,
        MessageID=message_id,
        UserMessage=user_message,
        BotResponse=bot_response,
        Rating=rating,
        Comment=comment
    )
    
    try:
        db.add(new_feedback)
        db.commit()
        db.refresh(new_feedback)
        
        return {
            "message": "Feedback submitted successfully",
            "feedback_id": new_feedback.FeedbackID
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {str(e)}"
        )

@router.get("/my-feedback", response_model=List[FeedbackResponse])
async def get_my_feedback(
    current_user: Union[Admin, User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get feedback submitted by the current user"""
    
    # Only users can view their own feedback
    if isinstance(current_user, Admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only users can view their feedback"
        )
    
    feedback_list = db.query(Feedback).filter(
        Feedback.UserID == current_user.UserID
    ).order_by(Feedback.CreatedAt.desc()).all()
    
    return [
        FeedbackResponse(
            feedback_id=feedback.FeedbackID,
            user_id=feedback.UserID,
            organization_id=feedback.OrganizationID,
            session_id=feedback.SessionID,
            message_id=feedback.MessageID,
            user_message=feedback.UserMessage,
            bot_response=feedback.BotResponse,
            rating=feedback.Rating,
            comment=feedback.Comment,
            created_at=feedback.CreatedAt,
            user_name=current_user.FullName,
            user_role=current_user.Role
        )
        for feedback in feedback_list
    ]

@router.get("/admin/users-feedback", response_model=List[FeedbackResponse])
async def get_users_feedback(
    current_user: Union[Admin, User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get feedback from all users managed by the current admin"""
    
    # Only admins can view their users' feedback
    if not isinstance(current_user, Admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view users' feedback"
        )
    
    # Get all users managed by this admin
    admin_users = db.query(User).filter(
        User.AdminID == current_user.AdminID
    ).all()
    
    user_ids = [user.UserID for user in admin_users]
    
    if not user_ids:
        return []
    
    # Get feedback from all users managed by this admin
    feedback_list = db.query(Feedback).filter(
        Feedback.UserID.in_(user_ids)
    ).order_by(Feedback.CreatedAt.desc()).all()
    
    # Get user details for each feedback
    user_details = {}
    for user in admin_users:
        user_details[user.UserID] = {
            "name": user.FullName,
            "role": user.Role
        }
    
    feedback_responses = []
    for feedback in feedback_list:
        # Debug: Print the raw feedback data
        print(f"🔍 Feedback {feedback.FeedbackID}:")
        print(f"   User message (raw): {repr(feedback.UserMessage)}")
        print(f"   Bot response (raw): {repr(feedback.BotResponse)}")
        
        feedback_responses.append(FeedbackResponse(
            feedback_id=feedback.FeedbackID,
            user_id=feedback.UserID,
            organization_id=feedback.OrganizationID,
            session_id=feedback.SessionID,
            message_id=feedback.MessageID,
            user_message=feedback.UserMessage,
            bot_response=feedback.BotResponse,
            rating=feedback.Rating,
            comment=feedback.Comment,
            created_at=feedback.CreatedAt,
            user_name=user_details.get(feedback.UserID, {}).get("name", "Unknown User"),
            user_role=user_details.get(feedback.UserID, {}).get("role", "Unknown Role")
        ))
    
    return feedback_responses

@router.get("/admin/feedback-stats", response_model=dict)
async def get_feedback_stats(
    current_user: Union[Admin, User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get feedback statistics for the admin's users"""
    
    # Only admins can view feedback stats
    if not isinstance(current_user, Admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view feedback statistics"
        )
    
    # Get all users managed by this admin
    admin_users = db.query(User).filter(
        User.AdminID == current_user.AdminID
    ).all()
    
    user_ids = [user.UserID for user in admin_users]
    
    if not user_ids:
        return {
            "total_feedback": 0,
            "average_rating": 0,
            "rating_distribution": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0},
            "total_users": 0
        }
    
    # Get feedback from all users managed by this admin
    feedback_list = db.query(Feedback).filter(
        Feedback.UserID.in_(user_ids)
    ).all()
    
    if not feedback_list:
        return {
            "total_feedback": 0,
            "average_rating": 0,
            "rating_distribution": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0},
            "total_users": len(user_ids)
        }
    
    # Calculate statistics
    total_feedback = len(feedback_list)
    total_rating = sum(feedback.Rating for feedback in feedback_list)
    average_rating = round(total_rating / total_feedback, 2)
    
    # Rating distribution
    rating_distribution = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
    for feedback in feedback_list:
        rating_distribution[str(feedback.Rating)] += 1
    
    return {
        "total_feedback": total_feedback,
        "average_rating": average_rating,
        "rating_distribution": rating_distribution,
        "total_users": len(user_ids)
    }
