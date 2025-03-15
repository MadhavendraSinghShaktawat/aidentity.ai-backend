"""
Authentication service for AIdentity.ai backend.

This module provides functions for user authentication and management.
"""
import logging
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, Tuple

from bson import ObjectId
from pydantic import EmailStr

from utils.auth import create_access_token, Token
from utils.config import Config
from utils.db import get_collection
from utils.errors import AuthenticationError, NotFoundError
from utils.oauth import GoogleOAuthProvider

# Configure logging
logger = logging.getLogger(__name__)

class AuthService:
    """Authentication service for user management."""
    
    @staticmethod
    async def generate_oauth_state() -> str:
        """
        Generates a random state for OAuth CSRF protection.
        
        Returns:
            str: Random state
        """
        return secrets.token_hex(16)
    
    @staticmethod
    async def get_google_auth_url(state: str) -> str:
        """
        Gets the Google OAuth authorization URL.
        
        Args:
            state: State parameter for CSRF protection
            
        Returns:
            str: Authorization URL
        """
        return GoogleOAuthProvider.get_authorization_url(state)
    
    @staticmethod
    async def authenticate_with_google(code: str) -> Token:
        """
        Authenticates a user with Google OAuth.
        
        Args:
            code: Authorization code from Google
            
        Returns:
            Token: Authentication token
            
        Raises:
            AuthenticationError: If authentication fails
        """
        # Get token and user info from Google
        token_response, user_info = await GoogleOAuthProvider.authenticate(code)
        
        # Extract user data
        google_id = user_info.get("sub")
        email = user_info.get("email")
        email_verified = user_info.get("email_verified", False)
        name = user_info.get("name")
        given_name = user_info.get("given_name")
        family_name = user_info.get("family_name")
        picture = user_info.get("picture")
        
        if not google_id or not email:
            raise AuthenticationError("Invalid user data from Google")
        
        # Check if user exists
        users_collection = get_collection("users")
        user = await users_collection.find_one({"email": email})
        
        # Create user if not exists
        if not user:
            # Generate username from email
            username = email.split("@")[0]
            
            # Check if username exists
            existing_user = await users_collection.find_one({"username": username})
            if existing_user:
                # Append random suffix to username
                username = f"{username}_{secrets.token_hex(4)}"
            
            # Create new user
            now = datetime.utcnow()
            user = {
                "_id": str(ObjectId()),
                "email": email,
                "username": username,
                "full_name": name,
                "role": "user",
                "preferences": {
                    "theme": "light",
                    "notifications_enabled": True,
                    "content_preferences": {}
                },
                "auth_provider": "google",
                "auth_provider_id": google_id,
                "is_active": True,
                "is_verified": email_verified,
                "profile_picture": picture,
                "created_at": now,
                "updated_at": now
            }
            
            # Insert user into database
            await users_collection.insert_one(user)
            logger.info(f"Created new user: {email}")
        else:
            # Update existing user
            now = datetime.utcnow()
            update_data = {
                "auth_provider": "google",
                "auth_provider_id": google_id,
                "is_verified": email_verified,
                "profile_picture": picture,
                "updated_at": now
            }
            
            # Update user in database
            await users_collection.update_one(
                {"_id": user["_id"]},
                {"$set": update_data}
            )
            logger.info(f"Updated existing user: {email}")
        
        # Create access token
        expires_delta = timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = await create_access_token(
            data={"sub": user["_id"], "email": email},
            expires_delta=expires_delta
        )
        
        # Return token
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=Config.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=user["_id"],
            email=email,
            username=user["username"],
            full_name=user.get("full_name")
        )
    
    @staticmethod
    async def get_user_by_id(user_id: str) -> Dict[str, Any]:
        """
        Gets a user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            Dict[str, Any]: User data
            
        Raises:
            NotFoundError: If user not found
        """
        users_collection = get_collection("users")
        user = await users_collection.find_one({"_id": user_id})
        
        if not user:
            raise NotFoundError(f"User not found: {user_id}")
        
        return user
    
    @staticmethod
    async def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        """
        Gets a user by email.
        
        Args:
            email: User email
            
        Returns:
            Optional[Dict[str, Any]]: User data or None if not found
        """
        users_collection = get_collection("users")
        return await users_collection.find_one({"email": email})
    
    @staticmethod
    async def update_user(user_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Updates a user.
        
        Args:
            user_id: User ID
            update_data: Data to update
            
        Returns:
            Dict[str, Any]: Updated user data
            
        Raises:
            NotFoundError: If user not found
        """
        users_collection = get_collection("users")
        
        # Check if user exists
        user = await users_collection.find_one({"_id": user_id})
        if not user:
            raise NotFoundError(f"User not found: {user_id}")
        
        # Update user
        now = datetime.utcnow()
        update_data["updated_at"] = now
        
        await users_collection.update_one(
            {"_id": user_id},
            {"$set": update_data}
        )
        
        # Get updated user
        updated_user = await users_collection.find_one({"_id": user_id})
        return updated_user 