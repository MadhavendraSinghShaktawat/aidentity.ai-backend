"""
API Routers Package

This package contains all API route definitions for the application.
Each module defines a specific set of related endpoints.
"""

import logging

# Configure logging
logger = logging.getLogger(__name__)

# This file can be empty, but it's required to make the directory a Python package
# You can optionally expose routers here for cleaner imports
from .auth_router import router as auth_router
from .test_router import router as test_router
from .trend_analyzer_router import router as trend_analyzer_router

__all__ = [
    "auth_router",
    "test_router",
    "trend_analyzer_router"
]

from typing import List

from fastapi import FastAPI

def register_routers(app: FastAPI) -> None:
    """
    Registers all API routers with the FastAPI application.
    
    Args:
        app: The FastAPI application instance
    """
    # Register auth router
    app.include_router(
        auth_router,
        prefix="/api/auth",
        tags=["auth"]
    )
    logger.info("Registered router: /api/auth")
    
    # Register test router
    app.include_router(
        test_router,
        prefix="/api/test",
        tags=["test"]
    )
    logger.info("Registered router: /api/test")
    
    # Register trend analyzer router
    app.include_router(
        trend_analyzer_router,
        prefix="/api/trend-analyzer",
        tags=["trend-analyzer"]
    )
    logger.info("Registered router: /api/trend-analyzer")
    
    logger.info("Registered 3 API routers")

# Import routers here once they're implemented
# This file can be empty for now or include router exports

# Example of how to export routers when they're ready:
# from .content import router as content_router
# from .trends import router as trends_router
# from .auth import router as auth_router

# __all__ = ["content_router", "trends_router", "auth_router"] 