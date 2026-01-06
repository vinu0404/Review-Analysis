"""
Admin dashboard API endpoints
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta
from typing import Optional
import uuid
import logging

from app.models import (
    AdminLoginRequest,
    AdminLoginResponse,
    ReviewsListResponse,
    AnalyticsResponse,
    ErrorResponse
)
from app.services.review_service import ReviewService
from app.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["Admin"])
security = HTTPBearer()
_active_tokens: dict = {}
review_service = ReviewService()


def generate_token() -> tuple[str, datetime]:
    """Generate a new session token"""
    settings = get_settings()
    token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(hours=settings.session_expire_hours)
    return token, expires_at


def validate_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Validate the bearer token"""
    token = credentials.credentials
    
    if token not in _active_tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token_data = _active_tokens[token]
    
    if datetime.utcnow() > token_data["expires_at"]:
        del _active_tokens[token]
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return token


@router.post(
    "/login",
    response_model=AdminLoginResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid credentials"}
    },
    summary="Admin login",
    description="Authenticate admin with password"
)
async def admin_login(request: AdminLoginRequest):
    """
    Admin login endpoint.
    
    - **password**: Admin password
    
    Returns session token on successful authentication.
    """
    settings = get_settings()
    
    if request.password != settings.admin_password:
        logger.warning("Failed admin login attempt")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
        )
    token, expires_at = generate_token()
    _active_tokens[token] = {
        "created_at": datetime.utcnow(),
        "expires_at": expires_at
    }
    
    logger.info("Admin logged in successfully")
    
    return AdminLoginResponse(
        success=True,
        message="Login successful",
        token=token,
        expires_in_hours=settings.session_expire_hours
    )


@router.post(
    "/logout",
    summary="Admin logout",
    description="Invalidate current session token"
)
async def admin_logout(token: str = Depends(validate_token)):
    """Logout and invalidate token"""
    if token in _active_tokens:
        del _active_tokens[token]
    
    return {"success": True, "message": "Logged out successfully"}


@router.get(
    "/reviews",
    response_model=ReviewsListResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"}
    },
    summary="Get all reviews",
    description="Get paginated list of all reviews with filters"
)
async def get_reviews(
    token: str = Depends(validate_token),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    rating: Optional[int] = Query(default=None, ge=1, le=5, description="Filter by rating"),
    search: Optional[str] = Query(default=None, description="Search in review text"),
    sort_by: str = Query(default="submission_time", description="Sort field"),
    sort_order: str = Query(default="desc", description="Sort order (asc/desc)")
):
    """
    Get paginated list of reviews.
    
    - **page**: Page number (starts from 1)
    - **page_size**: Number of items per page (max 100)
    - **rating**: Optional filter by star rating
    - **search**: Optional text search in reviews
    - **sort_by**: Field to sort by
    - **sort_order**: Sort direction (asc/desc)
    """
    try:
        result = await review_service.get_reviews(
            page=page,
            page_size=page_size,
            rating_filter=rating,
            search_query=search,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        return ReviewsListResponse(
            reviews=result["reviews"],
            total_count=result["total_count"],
            page=page,
            page_size=page_size,
            has_more=result["has_more"]
        )
        
    except Exception as e:
        logger.error(f"Error fetching reviews: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch reviews"
        )


@router.get(
    "/analytics",
    response_model=AnalyticsResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"}
    },
    summary="Get dashboard analytics",
    description="Get analytics data for admin dashboard"
)
async def get_analytics(token: str = Depends(validate_token)):
    """
    Get analytics for admin dashboard.
    
    Returns:
    - Total review count
    - Average rating
    - Rating distribution
    - Recent activity metrics
    """
    try:
        analytics = await review_service.get_analytics()
        
        return AnalyticsResponse(
            total_reviews=analytics["total_reviews"],
            average_rating=analytics["average_rating"],
            rating_distribution=analytics["rating_distribution"],
            reviews_today=analytics["reviews_today"],
            reviews_this_week=analytics["reviews_this_week"]
        )
        
    except Exception as e:
        logger.error(f"Error fetching analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch analytics"
        )


@router.get(
    "/health",
    summary="Health check",
    description="Check if admin API is healthy"
)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "admin-api",
        "timestamp": datetime.utcnow().isoformat(),
        "active_sessions": len(_active_tokens)
    }
