"""
Route module initialization
"""
from fastapi import APIRouter
from .auth import router as auth_router
from .organizations import router as org_router
from .admins import router as admin_router
from .users import router as user_router
from .system import router as system_router
from .chat import router as chat_router
from .documents import router as documents_router
from .feedback import router as feedback_router

# Create main router
router = APIRouter()

# Include all route groups
router.include_router(auth_router)
router.include_router(org_router)
router.include_router(admin_router)
router.include_router(user_router)
router.include_router(system_router)
router.include_router(chat_router)
router.include_router(documents_router)
router.include_router(feedback_router, prefix="/feedback", tags=["feedback"])

# Export the main router
__all__ = ["router"]
