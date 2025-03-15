"""
Minimal authentication router for testing.
"""
from fastapi import APIRouter

# Create router
router = APIRouter(
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)

@router.get("/login")
async def login():
    """
    Login endpoint.
    """
    return {"message": "Login endpoint"}

@router.get("/logout")
async def logout():
    """
    Logout endpoint.
    """
    return {"message": "Logout endpoint"} 