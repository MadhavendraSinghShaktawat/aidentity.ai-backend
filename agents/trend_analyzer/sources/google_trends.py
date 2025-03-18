"""
Google Trends Source

This module fetches trending topics from Google Trends API.
"""
import logging
import asyncio
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import urllib.parse
import json

import aiohttp
from fastapi import HTTPException

from ..schemas import TrendSource, TrendDepth

logger = logging.getLogger(__name__)

# Get Google OAuth configuration from environment variables
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")  # Not used in implicit flow
GOOGLE_REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:8001/redirect")
GOOGLE_SCOPES = "https://www.googleapis.com/auth/trends.readonly"

def get_oauth_authorization_url() -> str:
    """
    Generate the Google OAuth authorization URL with all required parameters.
    
    Returns:
        Properly formatted Google OAuth URL
        
    Raises:
        ValueError: If required credentials are missing
    """
    # Check if client ID is available
    if not GOOGLE_CLIENT_ID:
        error_msg = "GOOGLE_CLIENT_ID not set in environment variables. OAuth flow cannot proceed."
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Base URL for Google's OAuth
    base_url = "https://accounts.google.com/o/oauth2/auth"
    
    # Required parameters for the OAuth request
    params = {
        "response_type": "token",     # Required for implicit flow
        "client_id": GOOGLE_CLIENT_ID,  # Your OAuth client ID
        "redirect_uri": GOOGLE_REDIRECT_URI,  # Where to redirect after auth
        "scope": GOOGLE_SCOPES,       # What permissions to request
        "access_type": "offline",     # Get a refresh token
        "prompt": "consent"           # Always show consent screen
    }
    
    # Log the parameters (excluding sensitive information)
    safe_params = params.copy()
    logger.debug(f"OAuth parameters: {safe_params}")
    
    # Build the URL with proper URL encoding
    query_string = urllib.parse.urlencode(params)
    auth_url = f"{base_url}?{query_string}"
    
    # Log the generated URL (for debugging only)
    logger.debug(f"Generated OAuth URL: {auth_url}")
    
    return auth_url

async def fetch_google_trends(
    industry: str, 
    trend_depth: TrendDepth,
    keywords: Optional[List[str]] = None
) -> TrendSource:
    """
    Fetch trending topics from Google Trends based on industry and time range.
    
    Args:
        industry: The industry or niche to analyze
        trend_depth: How far back to analyze trends
        keywords: Optional list of specific keywords to focus on
        
    Returns:
        A TrendSource object with the raw Google Trends data
    """
    # For development and testing, we'll use mock data
    # In production, you would implement the actual API call
    logger.info(f"Fetching Google Trends for {industry} with depth {trend_depth}")
    
    # For OAuth flow testing, you can print the authorization URL:
    # logger.debug(f"Google OAuth URL: {get_oauth_authorization_url()}")
    
    # Set time range based on trend depth
    time_range = "now 1-d"  # Default to last 24 hours
    if trend_depth == "Past Week":
        time_range = "now 7-d"
    elif trend_depth == "Monthly":
        time_range = "today 1-m"
    
    # Generate mock data or fetch real data (when OAuth is set up)
    mock_data = _generate_mock_google_trends(industry, time_range, keywords)
    
    # Create and return the trend source object
    return TrendSource(
        platform="Google Trends",
        raw_data=mock_data,
        timestamp=datetime.utcnow(),
        metadata={
            "time_range": str(trend_depth),
            "is_mock": True,  # Flag to indicate this is mock data
            "keywords_used": keywords
        }
    )

def _generate_mock_google_trends(
    industry: str, 
    time_range: str,
    keywords: Optional[List[str]] = None
) -> str:
    """
    Generate mock Google Trends data for development.
    
    Args:
        industry: The industry or niche
        time_range: Time range for trends
        keywords: Optional list of specific keywords to focus on
        
    Returns:
        String containing mock Google Trends data
    """
    keyword_mention = f" with focus on {', '.join(keywords)}" if keywords else ""
    result = f"Google Trends data for {industry}{keyword_mention} over {time_range}:\n\n"
    
    # Current trending searches by industry
    industry_trends = {
        "tech": [
            "ChatGPT API price", 
            "Llama 3 release", 
            "NVIDIA AI chip", 
            "Google Gemini", 
            "Apple WWDC 2024"
        ],
        "fitness": [
            "Zone 2 training", 
            "Post-workout protein timing", 
            "Nordic hamstring curl", 
            "Fitness AR apps", 
            "Anti-aging workout"
        ],
        "business": [
            "Remote work policy", 
            "Layoffs tech industry", 
            "Startup funding 2024", 
            "Recession indicators", 
            "Digital nomad visa"
        ],
        "health": [
            "Long COVID symptoms", 
            "Ozempic side effects", 
            "Immune system boosters", 
            "Mental health apps", 
            "Circadian rhythm diet"
        ]
    }
    
    # Default trends if industry not found
    default_trends = [
        "Inflation rate", 
        "Climate change news", 
        "Summer vacation trends", 
        "Streaming service comparison", 
        "Work-life balance tips"
    ]
    
    # Get trends for the specific industry or use default
    normalized_industry = industry.lower()
    trends = []
    
    for ind, trend_list in industry_trends.items():
        if ind in normalized_industry or normalized_industry in ind:
            trends = trend_list
            break
    
    if not trends:
        trends = default_trends
    
    # If keywords provided, add some keyword-specific trends
    if keywords:
        keyword_trends = []
        for keyword in keywords[:3]:  # Use up to 3 keywords
            keyword_trends.append(f"{keyword} innovations 2024")
            keyword_trends.append(f"Best {keyword} tools")
            keyword_trends.append(f"{keyword} {industry} integration")
        
        # Add keyword trends to the beginning of the list
        trends = keyword_trends + trends
    
    # Create rising and top searches sections
    result += "RISING SEARCHES:\n"
    for i, trend in enumerate(trends[:5]):
        growth = 150 + (i * 50)  # Mock growth percentage
        result += f"{i+1}. \"{trend}\" - {growth}% growth\n"
    
    result += "\nTOP SEARCHES:\n"
    for i, trend in enumerate(trends[3:8]):  # Slight overlap with rising
        volume = 10000 - (i * 1000)  # Mock search volume
        result += f"{i+1}. \"{trend}\" - {volume:,} searches\n"
    
    # Add related topics
    result += "\nRELATED TOPICS:\n"
    related_topics = [
        f"{industry} news",
        f"{industry} 2024 trends",
        f"Best {industry} products",
        f"{industry} companies",
        f"{industry} innovations"
    ]
    
    for i, topic in enumerate(related_topics):
        result += f"{i+1}. {topic}\n"
    
    # Add geographic breakdown
    result += "\nGEOGRAPHIC INTEREST:\n"
    countries = ["United States", "United Kingdom", "India", "Canada", "Australia"]
    for i, country in enumerate(countries):
        score = 100 - (i * 15)
        result += f"{country}: {score}/100\n"
    
    return result

def validate_google_oauth_setup() -> Dict[str, Any]:
    """
    Validate the Google OAuth setup and return diagnostic information.
    
    This function checks if all required environment variables are set
    and returns information that can be used for debugging.
    
    Returns:
        Dictionary with validation results and diagnostic information
    """
    results = {
        "is_configured": False,
        "client_id_set": False,
        "client_id_valid": False,
        "redirect_uri_set": False,
        "redirect_uri_valid": False,
        "issues": [],
        "guidance": []
    }
    
    # Check client ID
    if not GOOGLE_CLIENT_ID:
        results["issues"].append("GOOGLE_CLIENT_ID environment variable is not set")
        results["guidance"].append("Add GOOGLE_CLIENT_ID=your_client_id_here to your .env file")
    else:
        results["client_id_set"] = True
        # Basic validation - client IDs are typically in a specific format
        if len(GOOGLE_CLIENT_ID) < 20 or "." not in GOOGLE_CLIENT_ID:
            results["issues"].append("GOOGLE_CLIENT_ID appears to be malformed")
            results["guidance"].append("Verify your client ID in the Google Cloud Console")
        else:
            results["client_id_valid"] = True
    
    # Check redirect URI
    if not GOOGLE_REDIRECT_URI:
        results["issues"].append("GOOGLE_REDIRECT_URI environment variable is not set")
        results["guidance"].append("Add GOOGLE_REDIRECT_URI=http://localhost:8001/redirect to your .env file")
    else:
        results["redirect_uri_set"] = True
        # Basic validation
        if not GOOGLE_REDIRECT_URI.startswith("http"):
            results["issues"].append("GOOGLE_REDIRECT_URI is not a valid URL")
            results["guidance"].append("Make sure your redirect URI starts with http:// or https://")
        else:
            results["redirect_uri_valid"] = True
    
    # Check if everything is properly configured
    if results["client_id_valid"] and results["redirect_uri_valid"]:
        results["is_configured"] = True
    
    # Provide the base URL for manual testing
    if results["client_id_valid"]:
        manual_url = (
            f"https://accounts.google.com/o/oauth2/auth?"
            f"response_type=token&"
            f"client_id={GOOGLE_CLIENT_ID}&"
            f"redirect_uri={urllib.parse.quote(GOOGLE_REDIRECT_URI)}&"
            f"scope={urllib.parse.quote(GOOGLE_SCOPES)}"
        )
        results["manual_test_url"] = manual_url
    
    return results

# Actual API implementation would go here
# For example:
# async def _fetch_google_trends_api(session, keywords, time_range):
#     # Make authenticated API calls to Google Trends
#     pass 