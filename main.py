"""
AIdentity.ai Backend API Entry Point

This module initializes the FastAPI application, configures middleware,
registers routes, and handles application lifecycle events.
"""
import logging
from typing import Dict, Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from utils.config import Config
from utils.errors import BaseAPIError
from routers.test_router import router as test_router
from routers.auth_router import router as auth_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create the FastAPI app
app = FastAPI(
    title="AIdentity.ai API",
    description="Backend API for AIdentity.ai content creation platform",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Debug: Print auth_router routes
logger.info("Auth router routes:")
for route in auth_router.routes:
    logger.info(f"  {route.path} [{route.methods}]")

# Debug: Print test_router routes
logger.info("Test router routes:")
for route in test_router.routes:
    logger.info(f"  {route.path} [{route.methods}]")

# Register routers directly
app.include_router(
    auth_router,
    prefix="/api/auth",
    tags=["auth"]
)
logger.info("Registered router: /api/auth")

app.include_router(
    test_router,
    prefix="/api/test",
    tags=["test"]
)
logger.info("Registered router: /api/test")

# Debug: Print all app routes
logger.info("All app routes:")
for route in app.routes:
    logger.info(f"  {route.path} [{route.methods if hasattr(route, 'methods') else 'N/A'}]")

# Add global exception handler
@app.exception_handler(BaseAPIError)
async def api_error_handler(request: Request, exc: BaseAPIError) -> JSONResponse:
    """
    Handles custom API errors and returns appropriate responses.
    
    Args:
        request: The incoming request
        exc: The exception that was raised
        
    Returns:
        JSONResponse: A formatted error response
    """
    logger.error(f"API Error: {exc.detail}", exc_info=True)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.error_code, "message": exc.detail},
    )

@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Simple health check endpoint.
    
    Returns:
        Dict[str, Any]: Health status information
    """
    return {
        "status": "healthy",
        "version": app.version,
        "environment": "development" if Config.DEV_MODE else "production"
    }

@app.get("/")
async def root():
    """
    Root endpoint that returns a simple message.
    
    Returns:
        dict: A simple message
    """
    return {"message": "Welcome to AIdentity.ai API"}

if __name__ == "__main__":
    import uvicorn
    
    # Use port 8001 instead of 8000 to avoid conflicts
    PORT = 8001
    
    uvicorn.run(
        "main:app",
        host=Config.HOST,
        port=PORT,  # Use the new port
        reload=Config.DEV_MODE
    ) 