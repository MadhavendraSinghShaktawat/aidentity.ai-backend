"""
MongoDB connection utilities for AIdentity.ai backend.

This module provides functions to connect to and disconnect from MongoDB.
"""
import logging
from typing import Any, Dict, Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from utils.config import Config

# Configure logging
logger = logging.getLogger(__name__)

# Global MongoDB client instance
mongo_client: Optional[AsyncIOMotorClient] = None
db: Optional[AsyncIOMotorDatabase] = None

async def connect_to_mongo() -> None:
    """
    Establishes connection to MongoDB.
    
    Raises:
        ConnectionFailure: If connection to MongoDB fails.
    """
    global mongo_client, db
    
    if mongo_client is not None:
        return
    
    try:
        logger.info(f"Connecting to MongoDB at {Config.MONGO_URI}...")
        mongo_client = AsyncIOMotorClient(Config.MONGO_URI, serverSelectionTimeoutMS=5000)
        
        # Verify connection
        await mongo_client.admin.command("ping")
        
        db = mongo_client[Config.DB_NAME]
        logger.info(f"Connected to MongoDB database: {Config.DB_NAME}")
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        raise

async def close_mongo_connection() -> None:
    """
    Closes the MongoDB connection.
    """
    global mongo_client
    
    if mongo_client is not None:
        logger.info("Closing MongoDB connection...")
        mongo_client.close()
        mongo_client = None
        logger.info("MongoDB connection closed")

def get_database() -> AsyncIOMotorDatabase:
    """
    Returns the database instance.
    
    Returns:
        AsyncIOMotorDatabase: The MongoDB database instance.
        
    Raises:
        ConnectionError: If database connection is not established.
    """
    if db is None:
        raise ConnectionError("Database connection not established")
    return db

def get_collection(collection_name: str):
    """
    Returns a specific collection from the database.
    
    Args:
        collection_name: Name of the collection to retrieve.
        
    Returns:
        Collection: The MongoDB collection.
    """
    database = get_database()
    return database[collection_name] 