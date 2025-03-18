"""
Middleware utilities for the FastAPI application.

This module provides custom middleware for request logging, error tracking,
and other cross-cutting concerns.
"""
import logging
import time
from typing import Callable, Dict, Any

from fastapi import Request, Response
from starlette.middleware.base import RequestResponseEndpoint

logger = logging.getLogger(__name__)

async def request_logging_middleware(request: Request, call_next: RequestResponseEndpoint) -> Response:
    """
    Middleware to log request information.
    
    Args:
        request: The incoming request
        call_next: The next middleware or route handler
        
    Returns:
        The response from the next middleware or route handler
    """
    start_time = time.time()
    path = request.url.path
    method = request.method
    
    # Log request start
    logger.info(f"Request started: {method} {path}")
    
    try:
        # Process the request through the next middleware or route handler
        response = await call_next(request)
        
        # Calculate and log processing time
        process_time = time.time() - start_time
        status_code = response.status_code
        logger.info(f"Request completed: {method} {path} - Status: {status_code} - Time: {process_time:.4f}s")
        
        return response
    except Exception as e:
        # Log error and re-raise
        process_time = time.time() - start_time
        logger.error(f"Request failed: {method} {path} - Error: {str(e)} - Time: {process_time:.4f}s")
        raise

async def error_tracking_middleware(request: Request, call_next: RequestResponseEndpoint) -> Response:
    """
    Middleware to track and handle errors.
    
    Args:
        request: The incoming request
        call_next: The next middleware or route handler
        
    Returns:
        The response from the next middleware or route handler
    """
    try:
        return await call_next(request)
    except Exception as e:
        # Log the error
        logger.exception(f"Unhandled exception in request: {str(e)}")
        
        # Optionally send to error tracking service (like Sentry)
        # This happens automatically if Sentry is configured
        
        # Re-raise the exception to let FastAPI handle it
        raise 