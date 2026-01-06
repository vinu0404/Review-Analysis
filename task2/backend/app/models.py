"""
Pydantic schemas for request/response validation
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum
class ReviewStatus(str, Enum):
    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"

class ReviewSubmissionRequest(BaseModel):
    """Schema for user review submission"""
    
    rating: int = Field(
        ge=1, 
        le=5, 
        description="Star rating from 1 to 5"
    )
    review_text: str = Field(
        min_length=10,
        max_length=1000,
        description="Review text (10-1000 characters)"
    )
    
    @field_validator('review_text')
    @classmethod
    def validate_not_empty_or_whitespace(cls, v: str) -> str:
        """Ensure review is not just whitespace"""
        stripped = v.strip()
        if len(stripped) < 10:
            raise ValueError("Review must contain at least 10 non-whitespace characters")
        return stripped
    
    class Config:
        json_schema_extra = {
            "example": {
                "rating": 5,
                "review_text": "The food was absolutely amazing! Great service too."
            }
        }


class ReviewSubmissionResponse(BaseModel):
    """Schema for review submission response"""
    
    success: bool = Field(description="Whether submission was successful")
    message: str = Field(description="Status message")
    user_response: str = Field(description="AI-generated response to user")
    submission_id: str = Field(description="Unique ID of the submission")
    processing_time_ms: int = Field(description="Total processing time in milliseconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Review submitted successfully",
                "user_response": "Thank you for your wonderful feedback! We're thrilled you enjoyed your experience.",
                "submission_id": "65a1b2c3d4e5f67890123456",
                "processing_time_ms": 2100
            }
        }


class AdminLoginRequest(BaseModel):
    """Schema for admin login"""
    
    password: str = Field(min_length=1, description="Admin password")
    
    class Config:
        json_schema_extra = {
            "example": {
                "password": "admin123"
            }
        }


class AdminLoginResponse(BaseModel):
    """Schema for admin login response"""
    
    success: bool
    message: str
    token: Optional[str] = None
    expires_in_hours: Optional[int] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Login successful",
                "token": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "expires_in_hours": 24
            }
        }


class ReviewMetadata(BaseModel):
    """Metadata for a review"""
    
    submission_time: datetime
    processing_time_ms: int
    llm_model: str
    status: ReviewStatus


class ReviewItem(BaseModel):
    """Schema for a single review item in admin dashboard"""
    
    id: str = Field(description="Review ID")
    rating: int = Field(ge=1, le=5)
    review_text: str
    user_response: str
    admin_summary: str
    recommended_actions: str
    submission_time: datetime
    status: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "65a1b2c3d4e5f67890123456",
                "rating": 5,
                "review_text": "Amazing food and service!",
                "user_response": "Thank you for your wonderful feedback!",
                "admin_summary": "Highly positive review praising food quality and service.",
                "recommended_actions": "• Continue maintaining high service standards\n• Consider featuring this review",
                "submission_time": "2026-01-06T10:30:00Z",
                "status": "processed"
            }
        }


class ReviewsListResponse(BaseModel):
    """Schema for paginated reviews list"""
    
    reviews: List[ReviewItem]
    total_count: int
    page: int
    page_size: int
    has_more: bool
    
    class Config:
        json_schema_extra = {
            "example": {
                "reviews": [],
                "total_count": 156,
                "page": 1,
                "page_size": 20,
                "has_more": True
            }
        }


class RatingDistribution(BaseModel):
    """Rating distribution for analytics"""
    
    star_1: int = Field(default=0, alias="1")
    star_2: int = Field(default=0, alias="2")
    star_3: int = Field(default=0, alias="3")
    star_4: int = Field(default=0, alias="4")
    star_5: int = Field(default=0, alias="5")


class AnalyticsResponse(BaseModel):
    """Schema for admin analytics"""
    
    total_reviews: int
    average_rating: float
    rating_distribution: Dict[str, int]
    reviews_today: int
    reviews_this_week: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_reviews": 156,
                "average_rating": 4.2,
                "rating_distribution": {
                    "1": 8,
                    "2": 12,
                    "3": 24,
                    "4": 47,
                    "5": 65
                },
                "reviews_today": 5,
                "reviews_this_week": 23
            }
        }


class ReviewDocument(BaseModel):
    """Schema for MongoDB document"""
    
    rating: int
    review_text: str
    user_response: str
    admin_summary: str
    recommended_actions: str
    metadata: ReviewMetadata


class ErrorResponse(BaseModel):
    """Schema for error responses"""
    
    success: bool = False
    error: str
    detail: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "Validation Error",
                "detail": "Review text must be at least 10 characters"
            }
        }
