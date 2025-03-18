from typing import List, Optional, Dict, Any
from datetime import date, datetime
from enum import Enum
from pydantic import BaseModel, Field

class CostMode(str, Enum):
    """Cost mode options for trend analysis."""
    LOW_COST = "Low-Cost"
    BALANCED = "Balanced"
    HIGH_QUALITY = "High-Quality"

class TrendDepth(str, Enum):
    """Time range options for trend analysis."""
    LAST_24H = "Latest 24h"
    PAST_WEEK = "Past Week"
    MONTHLY = "Monthly"

class CalendarDuration(str, Enum):
    """Duration options for content calendar."""
    WEEK = "7 Days"
    TWO_WEEKS = "14 Days"
    MONTH = "30 Days"

class TrendAnalyzerInput(BaseModel):
    """Input parameters for the trend analyzer agent."""
    target_platform: str = Field(..., description="Target social media platform (e.g., Instagram, Twitter)")
    industry: str = Field(..., description="Industry or niche for content (e.g., Tech, Fitness)")
    trend_depth: TrendDepth = Field(..., description="How far back to analyze trends")
    calendar_duration: CalendarDuration = Field(..., description="Duration of the content calendar")
    cost_mode: CostMode = Field(CostMode.BALANCED, description="Balance between cost and quality")
    bypass_cache: bool = Field(False, description="Whether to bypass cached results")
    keywords: Optional[List[str]] = Field(None, description="Specific keywords or topics to focus on (e.g., ['AI', 'machine learning', 'data science'])")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "target_platform": "Instagram",
                "industry": "Tech",
                "trend_depth": "Past Week",
                "calendar_duration": "7 Days",
                "cost_mode": "Balanced",
                "bypass_cache": False,
                "keywords": ["AI", "machine learning", "startup trends"]
            }
        }
    }

class TrendSource(BaseModel):
    """Data structure for trend source information."""
    platform: str = Field(..., description="Source platform name (Reddit, Twitter, etc.)")
    raw_data: str = Field(..., description="Raw trend data from the source")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the data was fetched")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional source metadata")

class TrendSummary(BaseModel):
    """Summarized trend information with insights."""
    topic: str = Field(..., description="Main trend topic")
    description: str = Field(..., description="Brief description of the trend")
    engagement_level: str = Field(..., description="Engagement level (HIGH, MEDIUM, LOW)")
    target_audience: str = Field(..., description="Key audience demographics for this trend")
    content_suggestions: List[str] = Field(..., description="Specific content ideas")
    source_platforms: List[str] = Field(..., description="Platforms where this trend is popular")
    timeliness: str = Field("ONGOING", description="How recent and timely this trend is (VERY_RECENT, RECENT, ONGOING)")

class ContentCalendarItem(BaseModel):
    """Individual content calendar item."""
    day_number: int = Field(..., description="Day number in the calendar")
    calendar_date: date = Field(..., description="Calendar date for this content")
    main_topic: str = Field(..., description="Main topic or theme")
    content_title: str = Field(..., description="Catchy title or headline")
    content_format: str = Field(..., description="Content format (post, story, video, etc.)")
    posting_time: str = Field(..., description="Recommended posting time")
    hashtags: List[str] = Field(..., description="Relevant hashtags")
    content_brief: str = Field(..., description="Brief description of content")

    model_config = {
        "json_schema_extra": {
            "example": {
                "day_number": 1,
                "calendar_date": "2024-03-20",
                "main_topic": "AI Technology Trends",
                "content_title": "The Future of AI in 2024",
                "content_format": "video",
                "posting_time": "10:00 AM",
                "hashtags": ["#AI", "#Technology", "#Future"],
                "content_brief": "An overview of emerging AI trends and their impact"
            }
        }
    }

class TrendAnalyzerOutput(BaseModel):
    """
    Output from the trend analyzer.
    """
    analyzed_at: datetime
    target_platform: str
    industry: str
    trend_depth: TrendDepth
    calendar_duration: str
    trend_summaries: List[TrendSummary]
    content_calendar: List[ContentCalendarItem]
    # Add a field to store the sources used in the analysis
    # The underscore prefix indicates this is somewhat internal/diagnostic
    _sources: Optional[List[TrendSource]] = None

class SupportedPlatformsResponse(BaseModel):
    """
    Response model for supported platforms and options.
    
    This provides information about the available platforms, trend depths,
    calendar durations, and cost modes for the Trend Analyzer.
    """
    platforms: List[str]
    trend_depths: List[str]
    calendar_durations: List[str]
    cost_modes: List[str] 