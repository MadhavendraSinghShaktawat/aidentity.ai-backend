"""
AIdentity.ai Backend API Entry Point

This module initializes the FastAPI application, configures middleware,
registers routes, and handles application lifecycle events.
"""
import logging
from typing import Dict, Any
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles

from utils.config import Config
from utils.errors import BaseAPIError
from utils.redis_cache import init_redis_pool, close_redis_pool
from routers.trend_analyzer_router import router as trend_analyzer_router
from routers.auth_router import router as auth_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Setup startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic - connect to databases, initialize services, etc.
    logging.info("Application starting up...")
    try:
        # Initialize Redis connection
        await init_redis_pool()
        logger.info("Application startup complete")
    except Exception as e:
        logger.error(f"Startup error: {str(e)}", exc_info=True)
        raise
    yield
    # Shutdown logic - close connections, cleanup resources, etc.
    logging.info("Application shutting down...")
    try:
        # Close Redis connection
        await close_redis_pool()
        logger.info("Application shutdown complete")
    except Exception as e:
        logger.error(f"Shutdown error: {str(e)}", exc_info=True)

# Create FastAPI app instance
app = FastAPI(
    title="AIdentity.ai API",
    description="Backend API for AIdentity.ai content creation platform",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/api-docs",
    redoc_url="/redoc",
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

# Debug: Print trend analyzer router routes
logger.info("Trend analyzer router routes:")
for route in trend_analyzer_router.routes:
    logger.info(f"  {route.path} [{route.methods}]")

# Debug: Print router info before registration
logger.info("=== ROUTER REGISTRATION STARTING ===")
logger.info(f"Auth router has {len(auth_router.routes)} routes")
logger.info(f"Trend analyzer router has {len(trend_analyzer_router.routes)} routes")

# Register routers with explicit tags and prefixes
app.include_router(trend_analyzer_router, prefix="/api/trend-analyzer", tags=["Trend Analyzer"])
logger.info("Registered router: /api/trend-analyzer")

app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
logger.info("Registered router: /api/auth")

# Debug: Print all registered routes
logger.info("All registered routes:")
for route in app.routes:
    if hasattr(route, "methods"):
        methods = ", ".join(route.methods)
        logger.info(f"  {route.path} [{methods}]")
    else:
        logger.info(f"  {route.path} [N/A]")

# Root endpoint
@app.get("/", tags=["Status"])
async def root():
    return {"status": "online", "message": "AIdentity.ai API is running"}

# Health check endpoint
@app.get("/health", tags=["Status"])
async def health_check():
    return {"status": "healthy"}

# Create a custom docs route with a more obvious name
@app.get("/api-docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - API Documentation",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
    )

# Keep the original docs route for compatibility
@app.get("/docs", include_in_schema=False)
async def get_documentation():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
    )

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

# This ensures the app is properly configured regardless of how it's started
if __name__ == "__main__":
    import uvicorn
    # Get port from environment or use default
    port = int(os.environ.get("PORT", 8001))
    host = os.environ.get("HOST", "0.0.0.0")
    
    # Run the application
    uvicorn.run("main:app", host=host, port=port, reload=True) 