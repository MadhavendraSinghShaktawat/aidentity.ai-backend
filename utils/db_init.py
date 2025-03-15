"""
MongoDB database initialization for AIdentity.ai backend.

This module provides functions to initialize the MongoDB database with
the required collections and indexes.
"""
import logging
from typing import List, Dict, Any

from utils.db import get_database

# Configure logging
logger = logging.getLogger(__name__)

async def create_collections() -> None:
    """
    Creates the required collections in the MongoDB database.
    """
    db = get_database()
    
    # List of collections to create
    collections = [
        "users",
        "content",
        "agents",
        "agent_runs",
        "media",
        "crawl_results"
    ]
    
    # Get existing collections
    existing_collections = await db.list_collection_names()
    
    # Create collections that don't exist
    for collection in collections:
        if collection not in existing_collections:
            logger.info(f"Creating collection: {collection}")
            await db.create_collection(collection)
        else:
            logger.info(f"Collection already exists: {collection}")

async def create_indexes() -> None:
    """
    Creates indexes for the MongoDB collections.
    """
    db = get_database()
    
    # Define indexes for each collection
    indexes = {
        "users": [
            {"keys": [("email", 1)], "unique": True},
            {"keys": [("username", 1)], "unique": True},
            {"keys": [("created_at", -1)]},
        ],
        "content": [
            {"keys": [("user_id", 1)]},
            {"keys": [("content_type", 1)]},
            {"keys": [("status", 1)]},
            {"keys": [("created_at", -1)]},
            {"keys": [("tags", 1)]},
        ],
        "agents": [
            {"keys": [("agent_type", 1)]},
            {"keys": [("model_provider", 1)]},
            {"keys": [("is_active", 1)]},
        ],
        "agent_runs": [
            {"keys": [("agent_id", 1)]},
            {"keys": [("user_id", 1)]},
            {"keys": [("content_id", 1)]},
            {"keys": [("status", 1)]},
            {"keys": [("created_at", -1)]},
        ],
        "media": [
            {"keys": [("user_id", 1)]},
            {"keys": [("content_id", 1)]},
            {"keys": [("created_at", -1)]},
        ],
        "crawl_results": [
            {"keys": [("user_id", 1)]},
            {"keys": [("url", 1)]},
            {"keys": [("created_at", -1)]},
        ],
    }
    
    # Create indexes for each collection
    for collection_name, collection_indexes in indexes.items():
        collection = db[collection_name]
        
        for index in collection_indexes:
            logger.info(f"Creating index on {collection_name}: {index['keys']}")
            await collection.create_index(**index)

async def initialize_database() -> None:
    """
    Initializes the MongoDB database with collections and indexes.
    """
    logger.info("Initializing MongoDB database...")
    
    try:
        await create_collections()
        await create_indexes()
        logger.info("MongoDB database initialization completed successfully")
    except Exception as e:
        logger.error(f"Failed to initialize MongoDB database: {str(e)}")
        raise 