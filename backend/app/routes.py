"""
Main API routes configuration
"""
from fastapi import APIRouter
from .routes.auth import router as auth_router
from .routes.organizations import router as org_router
from .routes.admins import router as admin_router
from .routes.users import router as user_router
from .routes.system import router as system_router

# Create main router
router = APIRouter()

# Include all route groups
router.include_router(auth_router)
router.include_router(org_router)
router.include_router(admin_router)
router.include_router(user_router)
router.include_router(system_router)
