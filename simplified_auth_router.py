"""
Simplified authentication router for AIdentity.ai backend.
"""
from fastapi import APIRouter

# Create router
router = APIRouter(
    tags=["auth"],
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