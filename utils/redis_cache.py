"""
This file provides Redis caching utilities for the application.
"""
import json
import logging
from typing import Any, Dict, Optional
from datetime import datetime, date

import redis

from utils.config import Config

logger = logging.getLogger(__name__)

# Initialize Redis connection (will be None in test environments)
redis_client = None

try:
    if not Config.DEV_MODE or Config.REDIS_HOST != "localhost":
        redis_client = redis.Redis(
            host=Config.REDIS_HOST,
            port=Config.REDIS_PORT,
            db=Config.REDIS_DB,
            password=Config.REDIS_PASSWORD,
            decode_responses=True
        )
        # Test connection
        redis_client.ping()
        logger.info(f"Redis connected at {Config.REDIS_HOST}:{Config.REDIS_PORT}")
    else:
        logger.info("Redis disabled in development mode or no Redis server configured")
except (redis.ConnectionError, redis.RedisError) as e:
    logger.warning(f"Failed to connect to Redis: {str(e)}")
    redis_client = None

async def get_cached_result(key: str) -> Optional[Dict[str, Any]]:
    """
    Get a cached result from Redis.
    
    Args:
        key: Cache key to retrieve
        
    Returns:
        The cached value or None if not found
    """
    if redis_client is None:
        logger.warning("Redis not initialized")
        return None
    
    try:
        # Attempt to get cached value
        cached = redis_client.get(key)
        if cached:
            logger.info(f"Cache hit for key: {key}")
            return json.loads(cached)
        logger.info(f"Cache miss for key: {key}")
        return None
    except Exception as e:
        logger.error(f"Error retrieving from cache: {str(e)}")
        return None

async def cache_result(key: str, data: Dict[str, Any], expiry_seconds: int = 3600) -> bool:
    """
    Cache a result in Redis.
    
    Args:
        key: Cache key
        data: Data to cache
        expiry_seconds: Time in seconds until the cache expires
        
    Returns:
        True if caching was successful, False otherwise
    """
    if redis_client is None:
        logger.warning("Redis not initialized")
        return False
    
    try:
        # Custom JSON serialization to handle datetime objects
        def json_serial(obj):
            """JSON serializer for objects not serializable by default json code"""
            if isinstance(obj, (datetime, date)):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")
            
        serialized = json.dumps(data, default=json_serial)
        redis_client.setex(key, expiry_seconds, serialized)
        logger.info(f"Cached result with key: {key} (expires in {expiry_seconds}s)")
        return True
    except Exception as e:
        logger.error(f"Error caching result: {str(e)}")
        return False

def close_redis_connection():
    """Close the Redis connection if it exists."""
    try:
        if redis_client is not None:
            redis_client.close()
            logger.info("Redis connection closed")
    except Exception as e:
        logger.error(f"Error closing Redis connection: {str(e)}") 