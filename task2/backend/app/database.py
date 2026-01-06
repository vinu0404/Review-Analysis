"""
MongoDB Atlas connection using Motor
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
import logging

from app.config import get_settings

logger = logging.getLogger(__name__)
_client: Optional[AsyncIOMotorClient] = None
_database: Optional[AsyncIOMotorDatabase] = None


async def connect_to_mongodb():
    """Initialize MongoDB connection"""
    global _client, _database
    
    settings = get_settings()
    
    try:
        logger.info("Connecting to MongoDB Atlas...")
        _client = AsyncIOMotorClient(
            settings.mongodb_uri,
            serverSelectionTimeoutMS=5000
        )
        
        await _client.admin.command('ping')
        
        _database = _client[settings.mongodb_db_name]
        await _create_indexes()
        
        logger.info(f"Connected to MongoDB database: {settings.mongodb_db_name}")
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise


async def _create_indexes():
    """Create database indexes for optimal query performance"""
    global _database
    
    if _database is None:
        return
    
    reviews_collection = _database.reviews
    await reviews_collection.create_index(
        [("metadata.submission_time", -1)],
        name="submission_time_desc"
    )
    await reviews_collection.create_index(
        [("rating", 1)],
        name="rating_filter"
    )
    
    await reviews_collection.create_index(
        [("metadata.status", 1), ("metadata.submission_time", -1)],
        name="status_time_compound"
    )
    
    logger.info("Database indexes created")


async def close_mongodb_connection():
    """Close MongoDB connection"""
    global _client
    
    if _client:
        _client.close()
        logger.info("MongoDB connection closed")


def get_database() -> AsyncIOMotorDatabase:
    """Get database instance"""
    global _database
    
    if _database is None:
        raise RuntimeError("Database not initialized. Call connect_to_mongodb() first.")
    
    return _database


def get_reviews_collection():
    """Get reviews collection"""
    return get_database().reviews
