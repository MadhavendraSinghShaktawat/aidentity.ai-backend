"""
Minimal FastAPI application to test minimal auth router.
"""
from fastapi import FastAPI
from minimal_auth_router import router as auth_router

# Create a minimal FastAPI app
app = FastAPI(
    title="Minimal API 2",
    description="A minimal API to test minimal auth router",
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
    return {"message": "Minimal API 2 is working"}

# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("minimal_app2:app", host="0.0.0.0", port=8004, reload=True) 