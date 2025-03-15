"""
Authentication utilities for AIdentity.ai backend.

This module provides functions for JWT token handling and user verification.
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr

from utils.config import Config
from utils.db import get_collection
from utils.errors import AuthenticationError

# Configure logging
logger = logging.getLogger(__name__)

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")

# Token model
class Token(BaseModel):
    """Token model for authentication."""
    access_token: str
    token_type: str
    expires_in: int
    user_id: str
    email: EmailStr
    username: str
    full_name: Optional[str] = None


class TokenData(BaseModel):
    """Token data model for JWT payload."""
    sub: str  # user_id
    email: EmailStr
    exp: int  # expiration timestamp


async def create_access_token(
    data: Dict[str, Any], 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Creates a JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Token expiration time
        
    Returns:
        str: JWT access token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    return jwt.encode(to_encode, Config.SECRET_KEY, algorithm="HS256")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    Verifies the JWT token and returns the current user.
    
    Args:
        token: JWT token
        
    Returns:
        Dict[str, Any]: User data
        
    Raises:
        AuthenticationError: If token is invalid or user not found
    """
    try:
        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        
        if user_id is None or email is None:
            raise AuthenticationError("Invalid authentication credentials")
        
        token_data = TokenData(sub=user_id, email=email, exp=payload.get("exp"))
    except JWTError:
        raise AuthenticationError("Invalid authentication credentials")
    
    # Get user from database
    users_collection = get_collection("users")
    user = await users_collection.find_one({"_id": user_id})
    
    if user is None:
        raise AuthenticationError("User not found")
    
    if not user.get("is_active", False):
        raise AuthenticationError("Inactive user")
    
    return user


async def get_optional_user(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[Dict[str, Any]]:
    """
    Verifies the JWT token and returns the current user if token is valid.
    
    Args:
        token: JWT token
        
    Returns:
        Optional[Dict[str, Any]]: User data or None if token is invalid
    """
    if token is None:
        return None
    
    try:
        return await get_current_user(token)
    except AuthenticationError:
        return None 