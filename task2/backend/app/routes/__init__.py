"""
Routes package initialization
"""

from app.routes.user import router as user_router
from app.routes.admin import router as admin_router

__all__ = ["user_router", "admin_router"]
