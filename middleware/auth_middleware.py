"""
Authentication middleware for AIdentity.ai backend.

This module provides middleware for handling JWT tokens.
"""
import logging
from typing import Callable, Optional

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware

from utils.config import Config
from utils.errors import AuthenticationError

# Configure logging
logger = logging.getLogger(__name__)

class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware for handling JWT tokens.
    
    This middleware extracts the JWT token from the Authorization header
    and adds the user ID to the request state if the token is valid.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Processes the request and adds the user ID to the request state.
        
        Args:
            request: The incoming request
            call_next: The next middleware or route handler
            
        Returns:
            Response: The response from the next middleware or route handler
        """
        # Skip authentication for public routes
        if self._is_public_route(request.url.path):
            return await call_next(request)
        
        # Get token from header
        authorization: str = request.headers.get("Authorization")
        
        if not authorization:
            # No token provided, continue without authentication
            return await call_next(request)
        
        try:
            # Extract token
            scheme, token = authorization.split()
            if scheme.lower() != "bearer":
                return await call_next(request)
            
            # Decode token
            payload = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
            user_id: str = payload.get("sub")
            
            if user_id:
                # Add user ID to request state
                request.state.user_id = user_id
        except (JWTError, ValueError) as e:
            # Invalid token, continue without authentication
            logger.warning(f"Invalid token: {str(e)}")
        
        return await call_next(request)
    
    def _is_public_route(self, path: str) -> bool:
        """
        Checks if the route is public (no authentication required).
        
        Args:
            path: The request path
            
        Returns:
            bool: True if the route is public, False otherwise
        """
        public_routes = [
            "/api/auth/login",
            "/api/auth/callback",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/metrics",
        ]
        
        for route in public_routes:
            if path.startswith(route):
                return True
        
        return False 