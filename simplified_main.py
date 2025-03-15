"""
Simplified AIdentity.ai Backend API Entry Point.
"""
from fastapi import FastAPI
from simplified_auth_router import router as auth_router

# Create the FastAPI app
app = FastAPI(
    title="Simplified AIdentity.ai API",
    description="Simplified Backend API for AIdentity.ai",
    version="0.1.0",
)

# Register router
app.include_router(
    auth_router,
    prefix="/api/auth",
    tags=["auth"]
)

@app.get("/")
async def root():
    """
    Root endpoint.
    """
    return {"message": "Simplified AIdentity.ai API is working"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("simplified_main:app", host="0.0.0.0", port=8007, reload=True) 