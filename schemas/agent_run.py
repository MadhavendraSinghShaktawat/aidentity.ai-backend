"""
Agent run schemas for AIdentity.ai backend.

This module defines Pydantic models for tracking AI agent runs.
"""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union, Any

from pydantic import BaseModel, Field


class RunStatus(str, Enum):
    """Run status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentRunBase(BaseModel):
    """Base agent run model."""
    agent_id: str
    user_id: str
    input_data: Dict[str, Any]
    content_id: Optional[str] = None


class AgentRunCreate(AgentRunBase):
    """Agent run creation model."""
    pass


class AgentRunUpdate(BaseModel):
    """Agent run update model."""
    status: Optional[RunStatus] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    completion_time_ms: Optional[int] = None
    tokens_used: Optional[int] = None


class AgentRun(AgentRunBase):
    """Agent run model with database fields."""
    id: str = Field(alias="_id")
    status: RunStatus = RunStatus.PENDING
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    completion_time_ms: Optional[int] = None
    tokens_used: Optional[int] = None
    cost: Optional[float] = None
    
    class Config:
        """Pydantic configuration."""
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "agent_id": "507f1f77bcf86cd799439012",
                "user_id": "507f1f77bcf86cd799439013",
                "content_id": "507f1f77bcf86cd799439014",
                "status": "completed",
                "input_data": {
                    "topic": "AI in healthcare",
                    "tone": "informative",
                    "length": "medium"
                },
                "output_data": {
                    "title": "The Revolutionary Impact of AI in Healthcare",
                    "content": "# The Revolutionary Impact of AI in Healthcare\n\nArtificial intelligence is transforming..."
                },
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:10Z",
                "completed_at": "2023-01-01T00:00:10Z",
                "completion_time_ms": 10000,
                "tokens_used": 1500,
                "cost": 0.03
            }
        } 