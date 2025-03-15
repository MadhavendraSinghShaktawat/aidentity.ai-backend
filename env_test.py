"""
Test script to check environment variables and their impact on FastAPI.
"""
import os
from fastapi import FastAPI
from pydantic import BaseSettings

class Settings(BaseSettings):
    """Application settings."""
    # Add any environment variables you want to check
    OPENAI_API_KEY: str = None
    ANTHROPIC_API_KEY: str = None
    GOOGLE_API_KEY: str = None
    
    class Config:
        env_file = ".env"

settings = Settings()

# Print environment variables
print("Environment variables:")
for key, value in settings.dict().items():
    print(f"  {key}: {'[SET]' if value else '[NOT SET]'}")

# Create a FastAPI app
app = FastAPI(
    title="Environment Test API",
    description="API to test environment variables",
    version="0.1.0",
)

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Environment Test API is working"}

@app.get("/env")
async def env():
    """Environment variables endpoint."""
    return {
        "env_vars": {
            key: "[SET]" if value else "[NOT SET]" 
            for key, value in settings.dict().items()
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("env_test:app", host="0.0.0.0", port=8006, reload=True) 