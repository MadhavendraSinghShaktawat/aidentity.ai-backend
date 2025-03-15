"""
Redis connection utilities for AIdentity.ai backend.

This module provides functions to connect to and disconnect from Redis.
"""
import logging
from typing import Optional

import redis.asyncio as redis
from redis.exceptions import ConnectionError as RedisConnectionError

from utils.config import Config

# Configure logging
logger = logging.getLogger(__name__)

# Global Redis client instance
redis_client: Optional[redis.Redis] = None

async def connect_to_redis() -> None:
    """
    Establishes connection to Redis.
    
    Raises:
        RedisConnectionError: If connection to Redis fails.
    """
    global redis_client
    
    if redis_client is not None:
        return
    
    try:
        logger.info(f"Connecting to Redis at {Config.REDIS_HOST}:{Config.REDIS_PORT}...")
        redis_client = redis.Redis(
            host=Config.REDIS_HOST,
            port=Config.REDIS_PORT,
            db=Config.REDIS_DB,
            password=Config.REDIS_PASSWORD,
            decode_responses=True
        )
        
        # Verify connection
        await redis_client.ping()
        
        logger.info("Connected to Redis")
    except RedisConnectionError as e:
        logger.error(f"Failed to connect to Redis: {str(e)}")
        raise

async def close_redis_connection() -> None:
    """
    Closes the Redis connection.
    """
    global redis_client
    
    if redis_client is not None:
        logger.info("Closing Redis connection...")
        await redis_client.close()
        redis_client = None
        logger.info("Redis connection closed")

def get_redis_client() -> redis.Redis:
    """
    Returns the Redis client instance.
    
    Returns:
        Redis: The Redis client instance.
        
    Raises:
        ConnectionError: If Redis connection is not established.
    """
    if redis_client is None:
        raise ConnectionError("Redis connection not established")
    return redis_client 