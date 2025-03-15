"""
Simple test FastAPI application to verify Swagger UI functionality.
"""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer
from pydantic import BaseModel

# Create a simple FastAPI app
app = FastAPI(
    title="Test API",
    description="A simple test API to verify Swagger UI functionality",
    version="0.1.0",
)

# Create a security scheme
token_auth_scheme = HTTPBearer()

# Define a simple model
class Item(BaseModel):
    name: str
    description: str = None
    price: float
    tax: float = None

# Define some routes
@app.get("/")
async def root():
    """
    Root endpoint that returns a simple message.
    
    Returns:
        dict: A simple message
    """
    return {"message": "Hello World"}

@app.get("/items/")
async def read_items():
    """
    Get all items.
    
    Returns:
        list: A list of items
    """
    return [{"name": "Item 1"}, {"name": "Item 2"}]

@app.post("/items/")
async def create_item(item: Item):
    """
    Create a new item.
    
    Args:
        item: The item to create
        
    Returns:
        Item: The created item
    """
    return item

@app.get("/secure")
async def secure_endpoint(token: str = Depends(token_auth_scheme)):
    """
    A secure endpoint that requires authentication.
    
    Args:
        token: The authentication token
        
    Returns:
        dict: The token credentials
    """
    return {"token": token.credentials}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("test_app:app", host="0.0.0.0", port=8001, reload=True) 