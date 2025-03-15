"""
Test FastAPI application with direct route definitions.
"""
from fastapi import FastAPI

app = FastAPI(
    title="Direct Routes API",
    description="API with direct route definitions",
    version="0.1.0",
)

@app.get("/")
async def root():
    """
    Root endpoint.
    """
    return {"message": "Direct Routes API is working"}

@app.get("/api/auth/login")
async def login():
    """
    Login endpoint.
    """
    return {"message": "Login endpoint"}

@app.get("/api/auth/logout")
async def logout():
    """
    Logout endpoint.
    """
    return {"message": "Logout endpoint"}

@app.get("/api/test/hello")
async def hello():
    """
    Hello endpoint.
    """
    return {"message": "Hello, World!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("direct_routes:app", host="0.0.0.0", port=8005, reload=True) 