"""
Configuration utilities for AIdentity.ai backend.

This module loads environment variables from the .env file and provides
a centralized configuration for the application.
"""
import logging
import os
import secrets
from typing import Any, Dict, Optional

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

def _clean_placeholder(value: Optional[str]) -> Optional[str]:
    """
    Cleans placeholder values from environment variables.
    
    Args:
        value: The environment variable value
        
    Returns:
        Optional[str]: None if the value is a placeholder, otherwise the value
    """
    if not value:
        return None
        
    # Common placeholder patterns
    placeholders = [
        "your_", "YOUR_", "placeholder_", "PLACEHOLDER_",
        "<your_", "<YOUR_", "<placeholder_", "<PLACEHOLDER_",
        "your-", "YOUR-", "placeholder-", "PLACEHOLDER-"
    ]
    
    for placeholder in placeholders:
        if value and value.startswith(placeholder):
            return None
            
    return value

class Config:
    """
    Application configuration loaded from environment variables.
    """
    # Development mode
    DEV_MODE: bool = os.getenv("DEV_MODE", "true").lower() == "true"
    
    # Server configuration
    PORT: int = int(os.getenv("PORT", "8000"))
    HOST: str = os.getenv("HOST", "0.0.0.0")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info")
    
    # MongoDB configuration
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    DB_NAME: str = os.getenv("DB_NAME", "aidentity")
    
    # Redis configuration
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: Optional[str] = _clean_placeholder(os.getenv("REDIS_PASSWORD"))
    
    # Authentication
    SECRET_KEY: str = _clean_placeholder(os.getenv("SECRET_KEY")) or secrets.token_hex(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    GOOGLE_CLIENT_ID: Optional[str] = _clean_placeholder(os.getenv("GOOGLE_CLIENT_ID"))
    GOOGLE_CLIENT_SECRET: Optional[str] = _clean_placeholder(os.getenv("GOOGLE_CLIENT_SECRET"))
    OAUTH_REDIRECT_URL: Optional[str] = _clean_placeholder(os.getenv("OAUTH_REDIRECT_URL"))
    
    # AI API keys
    OPENAI_API_KEY: Optional[str] = _clean_placeholder(os.getenv("OPENAI_API_KEY"))
    ANTHROPIC_API_KEY: Optional[str] = _clean_placeholder(os.getenv("ANTHROPIC_API_KEY"))
    GOOGLE_API_KEY: Optional[str] = _clean_placeholder(os.getenv("GOOGLE_API_KEY"))
    
    # Media processing
    S3_BUCKET_NAME: Optional[str] = _clean_placeholder(os.getenv("S3_BUCKET_NAME"))
    AWS_ACCESS_KEY_ID: Optional[str] = _clean_placeholder(os.getenv("AWS_ACCESS_KEY_ID"))
    AWS_SECRET_ACCESS_KEY: Optional[str] = _clean_placeholder(os.getenv("AWS_SECRET_ACCESS_KEY"))
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    
    # Third-party APIs
    HEYGEN_API_KEY: Optional[str] = _clean_placeholder(os.getenv("HEYGEN_API_KEY"))
    ELEVENLABS_API_KEY: Optional[str] = _clean_placeholder(os.getenv("ELEVENLABS_API_KEY"))
    TWITTER_API_KEY: Optional[str] = _clean_placeholder(os.getenv("TWITTER_API_KEY"))
    TWITTER_API_SECRET: Optional[str] = _clean_placeholder(os.getenv("TWITTER_API_SECRET"))
    REDDIT_CLIENT_ID: Optional[str] = _clean_placeholder(os.getenv("REDDIT_CLIENT_ID"))
    REDDIT_CLIENT_SECRET: Optional[str] = _clean_placeholder(os.getenv("REDDIT_CLIENT_SECRET"))
    
    # Monitoring
    SENTRY_DSN: Optional[str] = _clean_placeholder(os.getenv("SENTRY_DSN"))
    
    @classmethod
    def as_dict(cls) -> Dict[str, Any]:
        """
        Returns the configuration as a dictionary.
        
        Returns:
            Dict[str, Any]: Configuration dictionary
        """
        return {
            key: value for key, value in cls.__dict__.items()
            if not key.startswith("__") and not callable(value)
        }
    
    @classmethod
    def validate(cls) -> None:
        """
        Validates the configuration and logs warnings for missing values.
        """
        # Check required configuration in production
        if not cls.DEV_MODE:
            required_keys = [
                "MONGO_URI",
                "REDIS_HOST",
                "SECRET_KEY",
                "GOOGLE_CLIENT_ID",
                "GOOGLE_CLIENT_SECRET",
                "OPENAI_API_KEY",
                "ANTHROPIC_API_KEY",
                "GOOGLE_API_KEY",
            ]
            
            for key in required_keys:
                value = getattr(cls, key, None)
                if not value:
                    logger.warning(f"Missing required configuration: {key}")
        else:
            # Only check authentication keys in development mode
            auth_keys = [
                "SECRET_KEY",
                "GOOGLE_CLIENT_ID",
                "GOOGLE_CLIENT_SECRET",
            ]
            
            for key in auth_keys:
                value = getattr(cls, key, None)
                if not value:
                    logger.info(f"Missing authentication configuration: {key}")

# Validate configuration on module import
Config.validate() 