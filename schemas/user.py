"""
User schemas for AIdentity.ai backend.

This module defines Pydantic models for user data validation.
"""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    """User role enumeration."""
    ADMIN = "admin"
    USER = "user"
    CREATOR = "creator"


class UserPreferences(BaseModel):
    """User preferences model."""
    theme: str = "light"
    notifications_enabled: bool = True
    content_preferences: Dict[str, bool] = Field(default_factory=dict)


class UserBase(BaseModel):
    """Base user model."""
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    role: UserRole = UserRole.USER
    preferences: UserPreferences = Field(default_factory=UserPreferences)


class UserCreate(UserBase):
    """User creation model."""
    password: str


class UserUpdate(BaseModel):
    """User update model."""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    preferences: Optional[UserPreferences] = None


class User(UserBase):
    """User model with database fields."""
    id: str = Field(alias="_id")
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    is_verified: bool = False
    
    class Config:
        """Pydantic configuration."""
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "email": "user@example.com",
                "username": "johndoe",
                "full_name": "John Doe",
                "role": "user",
                "preferences": {
                    "theme": "dark",
                    "notifications_enabled": True,
                    "content_preferences": {
                        "technology": True,
                        "science": True
                    }
                },
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z",
                "is_active": True,
                "is_verified": True
            }
        } 