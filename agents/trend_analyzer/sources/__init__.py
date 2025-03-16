"""
Trend data source modules.

This package contains modules for fetching trending data from various platforms.
"""

from .reddit import fetch_reddit_trends
from .twitter import fetch_twitter_trends
from .youtube import fetch_youtube_trends
from .google_trends import fetch_google_trends
from .crawl4ai import fetch_crawl4ai_trends

__all__ = [
    "fetch_reddit_trends",
    "fetch_twitter_trends", 
    "fetch_youtube_trends",
    "fetch_google_trends",
    "fetch_crawl4ai_trends"
] 