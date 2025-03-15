"""
Simplified AIdentity.ai Backend API Entry Point for testing.
"""
import logging
from fastapi import FastAPI

from routers.simple_auth_router import router as auth_router
from routers.test_router import router as test_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create the FastAPI app
app = FastAPI(
    title="AIdentity.ai API (Simple)",
    description="Simplified Backend API for AIdentity.ai content creation platform",
    version="0.1.0",
)

# Register routers
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
    
    uvicorn.run(
        "simple_main:app",
        host="0.0.0.0",
        port=8002,
        reload=True
    ) 