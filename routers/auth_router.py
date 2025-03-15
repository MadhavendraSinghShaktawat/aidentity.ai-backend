"""
Authentication router for AIdentity.ai backend.

This module provides routes for user authentication.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2AuthorizationCodeBearer
from pydantic import BaseModel, EmailStr

from services.auth_service import AuthService
from utils.auth import Token, create_access_token, get_current_user, get_optional_user
from utils.config import Config
from utils.db import get_collection
from utils.errors import AuthenticationError

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)

# Define OAuth2 scheme for Google login
oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl="https://accounts.google.com/o/oauth2/auth",
    tokenUrl="https://oauth2.googleapis.com/token",
)

# Test login request model
class TestLoginRequest(BaseModel):
    email: EmailStr
    name: str = "Test User"

@router.post("/test-login")
async def test_login(request: TestLoginRequest):
    """
    Test login endpoint that doesn't require Google OAuth.
    This is for development and testing purposes only.
    
    Args:
        request: Login request with email and name
        
    Returns:
        Token: Authentication token
    """
    if not Config.DEV_MODE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Test login is only available in development mode"
        )
    
    try:
        # Check if user exists
        users_collection = get_collection("users")
        user = await users_collection.find_one({"email": request.email})
        
        # Create user if not exists
        if not user:
            # Generate username from email
            username = request.email.split("@")[0]
            
            # Check if username exists
            existing_user = await users_collection.find_one({"username": username})
            if existing_user:
                # Append random suffix to username
                import secrets
                username = f"{username}_{secrets.token_hex(4)}"
            
            # Create new user
            now = datetime.utcnow()
            user = {
                "_id": str(ObjectId()),
                "email": request.email,
                "username": username,
                "full_name": request.name,
                "role": "user",
                "preferences": {
                    "theme": "light",
                    "notifications_enabled": True,
                    "content_preferences": {}
                },
                "auth_provider": "test",
                "auth_provider_id": "test",
                "is_active": True,
                "is_verified": True,
                "profile_picture": None,
                "created_at": now,
                "updated_at": now
            }
            
            # Insert user into database
            await users_collection.insert_one(user)
            logger.info(f"Created new test user: {request.email}")
        
        # Create access token
        expires_delta = timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = await create_access_token(
            data={"sub": user["_id"], "email": request.email},
            expires_delta=expires_delta
        )
        
        # Return token
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=Config.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=user["_id"],
            email=request.email,
            username=user["username"],
            full_name=user.get("full_name")
        )
    except Exception as e:
        logger.exception(f"Test login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create test login: {str(e)}"
        )

@router.get("/login/google")
async def login_google() -> Dict[str, Any]:
    """
    Initiates Google OAuth login flow.
    
    Returns:
        Dict[str, Any]: Login URL and state information
    """
    return {
        "message": "Google login endpoint",
        "login_url": "https://accounts.google.com/o/oauth2/auth"
    }

@router.get("/callback/google")
async def google_callback(code: str) -> Dict[str, Any]:
    """
    Handles Google OAuth callback.
    
    Args:
        code: Authorization code from Google
        
    Returns:
        Dict[str, Any]: User information and access token
    """
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing authorization code"
        )
    
    # In a real implementation, you would exchange the code for tokens
    # and retrieve user information from Google
    
    return {
        "message": "Successfully authenticated with Google",
        "user": {
            "id": "sample_user_id",
            "email": "user@example.com"
        }
    }

@router.get("/logout")
async def logout() -> Dict[str, Any]:
    """
    Logs out the current user.
    
    Returns:
        Dict[str, Any]: Logout confirmation
    """
    return {"message": "Successfully logged out"}

@router.get("/me")
async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    Gets the current authenticated user.
    
    Args:
        token: OAuth access token
        
    Returns:
        Dict[str, Any]: User information
    """
    # In a real implementation, you would validate the token
    # and retrieve user information
    
    return {
        "id": "sample_user_id",
        "email": "user@example.com"
    } 