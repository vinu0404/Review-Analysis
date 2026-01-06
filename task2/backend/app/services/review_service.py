
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import logging
from bson import ObjectId

from app.database import get_reviews_collection
from app.models import ReviewItem

logger = logging.getLogger(__name__)


class ReviewService:
    """Service for handling review-related operations"""
    
    async def save_review(
        self,
        rating: int,
        review_text: str,
        user_response: str,
        admin_summary: str,
        recommended_actions: str,
        processing_time_ms: int,
        llm_model: str,
        status: str = "processed"
    ) -> str:
        """
        Save a new review to the database.
        
        Returns:
            The ID of the created document
        """
        collection = get_reviews_collection()
        
        document = {
            "rating": rating,
            "review_text": review_text,
            "user_response": user_response,
            "admin_summary": admin_summary,
            "recommended_actions": recommended_actions,
            "metadata": {
                "submission_time": datetime.utcnow(),
                "processing_time_ms": processing_time_ms,
                "llm_model": llm_model,
                "status": status
            }
        }
        
        result = await collection.insert_one(document)
        
        logger.info(f"Review saved with ID: {result.inserted_id}")
        
        return str(result.inserted_id)
    
    async def get_reviews(
        self,
        page: int = 1,
        page_size: int = 20,
        rating_filter: Optional[int] = None,
        search_query: Optional[str] = None,
        sort_by: str = "submission_time",
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """
        Get paginated reviews with optional filters.
        
        Returns:
            Dictionary with reviews list, total_count, and has_more flag
        """
        collection = get_reviews_collection()
        filter_query = {}
        
        if rating_filter is not None:
            filter_query["rating"] = rating_filter
        
        if search_query:
            filter_query["review_text"] = {
                "$regex": search_query,
                "$options": "i"  
            }
        skip = (page - 1) * page_size
        sort_direction = -1 if sort_order == "desc" else 1
        sort_field_map = {
            "submission_time": "metadata.submission_time",
            "rating": "rating",
            "status": "metadata.status"
        }
        sort_field = sort_field_map.get(sort_by, "metadata.submission_time")
        total_count = await collection.count_documents(filter_query)
        cursor = collection.find(filter_query)
        cursor = cursor.sort(sort_field, sort_direction)
        cursor = cursor.skip(skip).limit(page_size)
        
        reviews = []
        async for doc in cursor:
            reviews.append(ReviewItem(
                id=str(doc["_id"]),
                rating=doc["rating"],
                review_text=doc["review_text"],
                user_response=doc["user_response"],
                admin_summary=doc["admin_summary"],
                recommended_actions=doc["recommended_actions"],
                submission_time=doc["metadata"]["submission_time"],
                status=doc["metadata"]["status"]
            ))
        
        has_more = (skip + len(reviews)) < total_count
        
        return {
            "reviews": reviews,
            "total_count": total_count,
            "has_more": has_more
        }
    
    async def get_analytics(self) -> Dict[str, Any]:
        """
        Get analytics data for admin dashboard.
        
        Returns:
            Dictionary with analytics metrics
        """
        collection = get_reviews_collection()
        total_reviews = await collection.count_documents({})
        rating_pipeline = [
            {
                "$group": {
                    "_id": "$rating",
                    "count": {"$sum": 1}
                }
            }
        ]
        
        rating_distribution = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
        total_rating_sum = 0
        
        async for doc in collection.aggregate(rating_pipeline):
            rating = str(doc["_id"])
            count = doc["count"]
            rating_distribution[rating] = count
            total_rating_sum += doc["_id"] * count
        
        average_rating = round(total_rating_sum / total_reviews, 2) if total_reviews > 0 else 0.0
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        reviews_today = await collection.count_documents({
            "metadata.submission_time": {"$gte": today_start}
        })
        week_start = today_start - timedelta(days=today_start.weekday())
        reviews_this_week = await collection.count_documents({
            "metadata.submission_time": {"$gte": week_start}
        })
        
        return {
            "total_reviews": total_reviews,
            "average_rating": average_rating,
            "rating_distribution": rating_distribution,
            "reviews_today": reviews_today,
            "reviews_this_week": reviews_this_week
        }
    
    async def get_review_by_id(self, review_id: str) -> Optional[Dict[str, Any]]:
        """Get a single review by ID"""
        collection = get_reviews_collection()
        
        try:
            doc = await collection.find_one({"_id": ObjectId(review_id)})
            
            if doc:
                return {
                    "id": str(doc["_id"]),
                    "rating": doc["rating"],
                    "review_text": doc["review_text"],
                    "user_response": doc["user_response"],
                    "admin_summary": doc["admin_summary"],
                    "recommended_actions": doc["recommended_actions"],
                    "submission_time": doc["metadata"]["submission_time"],
                    "status": doc["metadata"]["status"]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching review {review_id}: {e}")
            return None
