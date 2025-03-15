"""
Simplified authentication router for AIdentity.ai backend.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

# Create router
router = APIRouter(
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)

# Test login request model
class TestLoginRequest(BaseModel):
    email: EmailStr
    name: str = "Test User"

@router.post("/test-login")
async def test_login(request: TestLoginRequest):
    """
    Test login endpoint that doesn't require Google OAuth.
    
    Args:
        request: Login request with email and name
        
    Returns:
        dict: A simple message
    """
    return {
        "message": f"Test login successful for {request.email}",
        "name": request.name
    }

@router.get("/login/google")
async def login_with_google():
    """
    Redirects to Google OAuth login page.
    
    Returns:
        dict: A simple message
    """
    return {"message": "This would redirect to Google OAuth login page"}

@router.get("/me")
async def get_current_user_info():
    """
    Gets the current authenticated user.
    
    Returns:
        dict: User data
    """
    return {
        "id": "test-user-id",
        "email": "test@example.com",
        "name": "Test User"
    }

@router.get("/logout")
async def logout():
    """
    Logs out the current user.
    
    Returns:
        dict: A simple message
    """
    return {"message": "Logged out successfully"} 