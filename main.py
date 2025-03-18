"""
AIdentity.ai Backend: Main application entry point.

This module initializes the FastAPI application and sets up routes, middleware, and dependencies.
"""
import logging
import os
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

# Import application components
from utils.config import Config
from utils.redis_cache import redis_client, close_redis_connection
from utils.middleware import request_logging_middleware, error_tracking_middleware

# Import routers from the routers package
from routers import auth_router, test_router, trend_analyzer_router

# For now, create empty router lists to allow the app to start
# We can uncomment these when the router files are ready
# Empty placeholder routers
content_router = APIRouter()
trends_router = APIRouter()

# Uncomment these when the router files exist:
# from routers.content import router as content_router
# from routers.trends import router as trends_router
# from routers.auth import router as auth_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("main")

# Initialize Sentry if configured
if Config.SENTRY_DSN:
    sentry_sdk.init(
        dsn=Config.SENTRY_DSN,
        traces_sample_rate=0.1,
        environment="production" if not Config.DEV_MODE else "development",
    )
    logger.info("Sentry initialized for error tracking")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages application startup and shutdown events.
    
    Args:
        app: The FastAPI application instance
    """
    # Startup
    logger.info("Application starting up...")
    
    # Yield control to the application
    yield
    
    # Shutdown
    logger.info("Application shutting down...")
    
    # Close Redis connection
    close_redis_connection()
    
    logger.info("Application shutdown complete")

# Create the FastAPI app
app = FastAPI(
    title="AIdentity.ai API",
    description="API for AI-driven content creation and automation",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Set to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(BaseHTTPMiddleware, dispatch=request_logging_middleware)
app.add_middleware(BaseHTTPMiddleware, dispatch=error_tracking_middleware)

# Include routers
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(test_router, prefix="/api/test", tags=["test"])
app.include_router(trend_analyzer_router, prefix="/api/trend-analyzer", tags=["trend-analyzer"])

@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify the API is running.
    
    Returns:
        dict: Status information
    """
    return {
        "status": "healthy",
        "version": "0.1.0",
        "environment": "production" if not Config.DEV_MODE else "development",
    }

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=Config.DEV_MODE,
    ) 