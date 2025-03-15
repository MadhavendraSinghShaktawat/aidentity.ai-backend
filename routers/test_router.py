"""
Test router for AIdentity.ai backend.

This module provides test routes for development and debugging.
"""
import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    tags=["test"],
    responses={404: {"description": "Not found"}},
)

@router.get("/hello")
async def hello() -> Dict[str, str]:
    """
    Simple hello world endpoint.
    
    Returns:
        Dict[str, str]: A greeting message
    """
    return {"message": "Hello, World!"}

@router.get("/echo/{message}")
async def echo(message: str) -> Dict[str, str]:
    """
    Echoes back the provided message.
    
    Args:
        message: The message to echo
        
    Returns:
        Dict[str, str]: The echoed message
    """
    return {"message": message}

@router.get("/status")
async def status() -> Dict[str, Any]:
    """
    Returns the current API status.
    
    Returns:
        Dict[str, Any]: Status information
    """
    return {
        "status": "operational",
        "version": "0.1.0",
        "endpoints": {
            "hello": "/api/test/hello",
            "echo": "/api/test/echo/{message}",
            "status": "/api/test/status"
        }
    }

@router.get("/")
async def test_endpoint():
    """
    Simple test endpoint to verify that the API is working.
    
    Returns:
        dict: A simple message
    """
    return {"message": "API is working!"}

@router.get("/auth")
async def test_auth_endpoint():
    """
    Simple test endpoint to verify that the auth routes are registered.
    
    Returns:
        dict: A simple message
    """
    return {
        "message": "Auth routes should be working!",
        "auth_routes": [
            "/api/auth/login/google",
            "/api/auth/callback/google",
            "/api/auth/me",
            "/api/auth/logout"
        ]
    } 