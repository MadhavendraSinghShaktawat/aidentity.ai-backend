"""
Agent schemas for AIdentity.ai backend.

This module defines Pydantic models for AI agent data validation.
"""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field


class AgentType(str, Enum):
    """Agent type enumeration."""
    IDEATION = "ideation"
    SCRIPTING = "scripting"
    EDITING = "editing"
    RESEARCH = "research"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"


class ModelProvider(str, Enum):
    """Model provider enumeration."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"


class AgentBase(BaseModel):
    """Base agent model."""
    name: str
    description: str
    agent_type: AgentType
    model_provider: ModelProvider
    model_name: str
    parameters: Dict[str, Union[str, int, float, bool, List[str]]] = Field(default_factory=dict)
    is_active: bool = True


class AgentCreate(AgentBase):
    """Agent creation model."""
    pass


class AgentUpdate(BaseModel):
    """Agent update model."""
    name: Optional[str] = None
    description: Optional[str] = None
    agent_type: Optional[AgentType] = None
    model_provider: Optional[ModelProvider] = None
    model_name: Optional[str] = None
    parameters: Optional[Dict[str, Union[str, int, float, bool, List[str]]]] = None
    is_active: Optional[bool] = None


class Agent(AgentBase):
    """Agent model with database fields."""
    id: str = Field(alias="_id")
    created_at: datetime
    updated_at: datetime
    usage_count: int = 0
    average_response_time_ms: Optional[float] = None
    
    class Config:
        """Pydantic configuration."""
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "name": "Blog Post Generator",
                "description": "Generates blog post content from a topic and outline",
                "agent_type": "scripting",
                "model_provider": "openai",
                "model_name": "gpt-3.5-turbo",
                "parameters": {
                    "temperature": 0.7,
                    "max_tokens": 2000,
                    "top_p": 1.0
                },
                "is_active": True,
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z",
                "usage_count": 150,
                "average_response_time_ms": 2500.5
            }
        } 