"""
OAuth providers for AIdentity.ai backend.

This module provides OAuth providers for authentication.
"""
import logging
from typing import Dict, Optional, Any, Tuple
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException, status

from utils.config import Config
from utils.errors import AuthenticationError

# Configure logging
logger = logging.getLogger(__name__)

class GoogleOAuthProvider:
    """Google OAuth provider for authentication."""
    
    # Google OAuth endpoints
    AUTH_URL = "https://accounts.google.com/o/oauth2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USER_INFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
    
    @classmethod
    def get_authorization_url(cls, state: str) -> str:
        """
        Generates the Google OAuth authorization URL.
        
        Args:
            state: State parameter for CSRF protection
            
        Returns:
            str: Authorization URL
        """
        if not Config.GOOGLE_CLIENT_ID or not Config.OAUTH_REDIRECT_URL:
            raise AuthenticationError("Google OAuth is not configured")
        
        params = {
            "client_id": Config.GOOGLE_CLIENT_ID,
            "redirect_uri": Config.OAUTH_REDIRECT_URL,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
        }
        
        return f"{cls.AUTH_URL}?{urlencode(params)}"
    
    @classmethod
    async def exchange_code_for_token(cls, code: str) -> Dict[str, Any]:
        """
        Exchanges the authorization code for an access token.
        
        Args:
            code: Authorization code from Google
            
        Returns:
            Dict[str, Any]: Token response
            
        Raises:
            AuthenticationError: If token exchange fails
        """
        if not Config.GOOGLE_CLIENT_ID or not Config.GOOGLE_CLIENT_SECRET or not Config.OAUTH_REDIRECT_URL:
            raise AuthenticationError("Google OAuth is not configured")
        
        data = {
            "client_id": Config.GOOGLE_CLIENT_ID,
            "client_secret": Config.GOOGLE_CLIENT_SECRET,
            "redirect_uri": Config.OAUTH_REDIRECT_URL,
            "code": code,
            "grant_type": "authorization_code",
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(cls.TOKEN_URL, data=data)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"Failed to exchange code for token: {str(e)}")
                logger.error(f"Response: {e.response.text if hasattr(e, 'response') else 'No response'}")
                raise AuthenticationError("Failed to authenticate with Google")
    
    @classmethod
    async def get_user_info(cls, access_token: str) -> Dict[str, Any]:
        """
        Gets user information from Google.
        
        Args:
            access_token: Access token from Google
            
        Returns:
            Dict[str, Any]: User information
            
        Raises:
            AuthenticationError: If user info retrieval fails
        """
        headers = {"Authorization": f"Bearer {access_token}"}
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(cls.USER_INFO_URL, headers=headers)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"Failed to get user info: {str(e)}")
                raise AuthenticationError("Failed to get user information from Google")
    
    @classmethod
    async def authenticate(cls, code: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Authenticates a user with Google OAuth.
        
        Args:
            code: Authorization code from Google
            
        Returns:
            Tuple[Dict[str, Any], Dict[str, Any]]: Token response and user info
            
        Raises:
            AuthenticationError: If authentication fails
        """
        token_response = await cls.exchange_code_for_token(code)
        access_token = token_response.get("access_token")
        
        if not access_token:
            raise AuthenticationError("Failed to get access token from Google")
        
        user_info = await cls.get_user_info(access_token)
        
        return token_response, user_info 