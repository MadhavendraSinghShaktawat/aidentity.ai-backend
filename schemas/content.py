"""
Content schemas for AIdentity.ai backend.

This module defines Pydantic models for content data validation.
"""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field, HttpUrl


class ContentType(str, Enum):
    """Content type enumeration."""
    BLOG = "blog"
    SOCIAL = "social"
    VIDEO = "video"
    AUDIO = "audio"
    IMAGE = "image"


class ContentStatus(str, Enum):
    """Content status enumeration."""
    DRAFT = "draft"
    PROCESSING = "processing"
    READY = "ready"
    PUBLISHED = "published"
    FAILED = "failed"


class MediaInfo(BaseModel):
    """Media information model."""
    url: HttpUrl
    mime_type: str
    size_bytes: int
    duration_seconds: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    thumbnail_url: Optional[HttpUrl] = None


class ContentBase(BaseModel):
    """Base content model."""
    title: str
    description: Optional[str] = None
    content_type: ContentType
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Union[str, int, float, bool]] = Field(default_factory=dict)


class ContentCreate(ContentBase):
    """Content creation model."""
    user_id: str
    prompt: str
    references: List[HttpUrl] = Field(default_factory=list)


class ContentUpdate(BaseModel):
    """Content update model."""
    title: Optional[str] = None
    description: Optional[str] = None
    content_type: Optional[ContentType] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Union[str, int, float, bool]]] = None
    status: Optional[ContentStatus] = None
    content: Optional[str] = None
    media: Optional[MediaInfo] = None


class Content(ContentBase):
    """Content model with database fields."""
    id: str = Field(alias="_id")
    user_id: str
    status: ContentStatus = ContentStatus.DRAFT
    content: Optional[str] = None
    media: Optional[MediaInfo] = None
    prompt: str
    references: List[HttpUrl] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None
    model_used: Optional[str] = None
    
    class Config:
        """Pydantic configuration."""
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "user_id": "507f1f77bcf86cd799439012",
                "title": "The Future of AI",
                "description": "An exploration of AI trends in 2023",
                "content_type": "blog",
                "tags": ["AI", "technology", "future"],
                "status": "published",
                "content": "# The Future of AI\n\nArtificial intelligence is transforming...",
                "media": {
                    "url": "https://example.com/media/image.jpg",
                    "mime_type": "image/jpeg",
                    "size_bytes": 1024000,
                    "width": 1920,
                    "height": 1080,
                    "thumbnail_url": "https://example.com/media/image_thumb.jpg"
                },
                "prompt": "Write a blog post about the future of AI in 2023",
                "references": ["https://example.com/reference1"],
                "metadata": {
                    "word_count": 1500,
                    "reading_time_minutes": 7.5
                },
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z",
                "published_at": "2023-01-02T00:00:00Z",
                "model_used": "gpt-3.5-turbo"
            }
        } 