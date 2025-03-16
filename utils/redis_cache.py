import json
from typing import Any, Optional
from datetime import timedelta
import logging
from fastapi import HTTPException
from redis.asyncio import Redis

logger = logging.getLogger(__name__)

# Redis connection instance
redis: Optional[Redis] = None

async def init_redis_pool() -> None:
    """Initialize the Redis connection pool."""
    global redis
    try:
        redis = Redis.from_url(
            "redis://localhost",
            encoding="utf-8",
            decode_responses=True
        )
        await redis.ping()
        logger.info("Successfully connected to Redis")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to connect to Redis cache")

async def close_redis_pool() -> None:
    """Close the Redis connection pool."""
    if redis:
        await redis.close()
        logger.info("Redis connection closed")

async def get_cached_result(key: str) -> Optional[dict]:
    """
    Retrieve a cached result from Redis.
    
    Args:
        key: The cache key to retrieve
        
    Returns:
        The cached data as a dictionary if found, None otherwise
    """
    if not redis:
        logger.warning("Redis not initialized")
        return None
    
    try:
        cached_data = await redis.get(key)
        if cached_data:
            return json.loads(cached_data)
        return None
    except Exception as e:
        logger.error(f"Error retrieving from cache: {str(e)}")
        return None

async def cache_result(key: str, data: Any, expiry_seconds: int = 3600) -> bool:
    """
    Cache data in Redis with an expiration time.
    
    Args:
        key: The cache key
        data: The data to cache (must be JSON serializable)
        expiry_seconds: Time in seconds before the cache expires (default: 1 hour)
        
    Returns:
        True if caching was successful, False otherwise
    """
    if not redis:
        logger.warning("Redis not initialized")
        return False
    
    try:
        serialized_data = json.dumps(data)
        await redis.set(
            key,
            serialized_data,
            ex=expiry_seconds
        )
        return True
    except Exception as e:
        logger.error(f"Error caching result: {str(e)}")
        return False

async def invalidate_cache(key: str) -> bool:
    """
    Remove a specific key from the cache.
    
    Args:
        key: The cache key to invalidate
        
    Returns:
        True if invalidation was successful, False otherwise
    """
    if not redis:
        logger.warning("Redis not initialized")
        return False
    
    try:
        await redis.delete(key)
        return True
    except Exception as e:
        logger.error(f"Error invalidating cache: {str(e)}")
        return False 