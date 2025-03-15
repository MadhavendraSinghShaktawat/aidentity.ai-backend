"""
Minimal FastAPI application to test auth router.
"""
from fastapi import FastAPI
from routers.auth_router import router as auth_router

# Create a minimal FastAPI app
app = FastAPI(
    title="Minimal API",
    description="A minimal API to test auth router",
    version="0.1.0",
)

# Register auth router
app.include_router(
    auth_router,
    prefix="/api/auth",
    tags=["auth"]
)

# Add a root endpoint
@app.get("/")
async def root():
    """
    Root endpoint.
    """
    return {"message": "Minimal API is working"}

# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("minimal_app:app", host="0.0.0.0", port=8003, reload=True) 