"""
Basic FastAPI application with direct route definitions.
"""
from fastapi import FastAPI

# Create a basic FastAPI app
app = FastAPI()

@app.get("/")
def root():
    """Root endpoint."""
    return {"message": "Hello World"}

@app.get("/api/public")
def public():
    """Public endpoint."""
    return {"message": "This is a public endpoint"}

@app.get("/api/test")
def test():
    """Test endpoint."""
    return {"message": "This is a test endpoint"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("basic_app:app", host="0.0.0.0", port=8010, reload=True) 