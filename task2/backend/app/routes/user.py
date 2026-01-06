"""
User-facing API endpoints
"""

from fastapi import APIRouter, HTTPException, status
from datetime import datetime
import time
import logging

from app.models import (
    ReviewSubmissionRequest,
    ReviewSubmissionResponse,
    ErrorResponse
)
from app.services.review_service import ReviewService
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/user", tags=["User"])
review_service = ReviewService()
llm_service = LLMService()


@router.post(
    "/submit-review",
    response_model=ReviewSubmissionResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Validation Error"},
        500: {"model": ErrorResponse, "description": "Server Error"},
        503: {"model": ErrorResponse, "description": "LLM Service Unavailable"}
    },
    summary="Submit a new review",
    description="Submit a user review with rating (1-5) and review text. Returns AI-generated response."
)
async def submit_review(request: ReviewSubmissionRequest):
    """
    Submit a new review and receive AI-generated response.
    
    - **rating**: Star rating from 1 to 5
    - **review_text**: Review text (10-1000 characters)
    
    Returns AI-generated response and stores review with admin summary.
    """
    start_time = time.time()
    
    try:
        logger.info(f"Received review submission: rating={request.rating}, text_length={len(request.review_text)}")
        
        llm_results = await llm_service.process_review(
            rating=request.rating,
            review_text=request.review_text
        )
        processing_time_ms = int((time.time() - start_time) * 1000)
        submission_id = await review_service.save_review(
            rating=request.rating,
            review_text=request.review_text,
            user_response=llm_results["user_response"],
            admin_summary=llm_results["admin_summary"],
            recommended_actions=llm_results["recommended_actions"],
            processing_time_ms=processing_time_ms,
            llm_model=llm_results["model_used"]
        )
        
        logger.info(f"Review saved successfully: {submission_id}")
        
        return ReviewSubmissionResponse(
            success=True,
            message="Review submitted successfully! Thank you for your feedback.",
            user_response=llm_results["user_response"],
            submission_id=submission_id,
            processing_time_ms=processing_time_ms
        )
        
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
        
    except Exception as e:
        logger.error(f"Error processing review: {e}")
        try:
            fallback_response = llm_service.get_fallback_response(request.rating)
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            submission_id = await review_service.save_review(
                rating=request.rating,
                review_text=request.review_text,
                user_response=fallback_response,
                admin_summary="[Processing failed - manual review needed]",
                recommended_actions="[Processing failed - manual review needed]",
                processing_time_ms=processing_time_ms,
                llm_model="fallback",
                status="failed"
            )
            
            return ReviewSubmissionResponse(
                success=True,
                message="Review submitted successfully!",
                user_response=fallback_response,
                submission_id=submission_id,
                processing_time_ms=processing_time_ms
            )
            
        except Exception as save_error:
            logger.error(f"Failed to save review: {save_error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to process your review. Please try again later."
            )


@router.get(
    "/health",
    summary="Health check",
    description="Check if user API is healthy"
)
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "user-api", "timestamp": datetime.utcnow().isoformat()}
