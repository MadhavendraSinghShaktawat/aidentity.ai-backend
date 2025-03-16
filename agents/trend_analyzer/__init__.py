"""
Trend Analyzer Agent

This module provides functionality to analyze trending topics across 
multiple platforms and generate content calendars based on those trends.
"""

from .agent import analyze_trends
from .schemas import (
    TrendAnalyzerInput,
    TrendAnalyzerOutput,
    ContentCalendarItem,
    TrendSummary,
    CostMode,
    TrendDepth,
    CalendarDuration
)

__all__ = [
    "analyze_trends",
    "TrendAnalyzerInput",
    "TrendAnalyzerOutput",
    "ContentCalendarItem",
    "TrendSummary",
    "CostMode",
    "TrendDepth",
    "CalendarDuration"
] 