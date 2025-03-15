"""
Router package initialization.
This file ensures that the routers package is properly initialized.
"""

# Configure logging
logger = logging.getLogger(__name__)

# This file can be empty, but it's required to make the directory a Python package
# You can optionally expose routers here for cleaner imports
from routers.auth_router import router as auth_router
from routers.test_router import router as test_router

__all__ = ["auth_router", "test_router"]

import logging
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
    
    logger.info("Registered 2 API routers") 