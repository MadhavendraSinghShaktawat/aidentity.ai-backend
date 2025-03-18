"""
Google Trends Source

This module fetches trending topics from Google Trends API.
"""
import logging
import asyncio
import os
import warnings
from typing import List, Dict, Any, Optional
from datetime import datetime
import urllib.parse
import json
import concurrent.futures
import time

# Suppress pandas FutureWarning about downcasting
warnings.filterwarnings("ignore", category=FutureWarning, module="pandas")

import aiohttp
from fastapi import HTTPException
import pandas as pd

# Import pytrends for real Google Trends access
from pytrends.request import TrendReq

from ..schemas import TrendSource, TrendDepth

logger = logging.getLogger(__name__)

# Get Google OAuth configuration from environment variables
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")  # Not used in implicit flow
GOOGLE_REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:8001/redirect")
GOOGLE_SCOPES = "https://www.googleapis.com/auth/trends.readonly"

# Set pandas option to avoid the FutureWarning
pd.set_option('future.no_silent_downcasting', True)

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
    logger.info(f"Fetching Google Trends for {industry} with depth {trend_depth}")
    
    # Set time range based on trend depth
    time_range = "now 1-d"  # Default to last 24 hours
    if trend_depth == TrendDepth.PAST_WEEK:
        time_range = "now 7-d"
    elif trend_depth == TrendDepth.MONTHLY:
        time_range = "today 1-m"
    
    try:
        # Try to fetch trending topics first - these are the most viral
        raw_data = await _fetch_viral_trends(industry, time_range, keywords)
        is_mock = False
        logger.info("Successfully fetched viral Google Trends data")
    except Exception as e:
        logger.warning(f"Failed to fetch viral trends: {str(e)}. Trying regular trends.")
        
        try:
            # Fallback to regular Google Trends data
            raw_data = await _fetch_real_google_trends(industry, time_range, keywords)
            is_mock = False
            logger.info("Successfully fetched real Google Trends data")
        except Exception as e:
            # If both methods fail, fall back to mock data
            logger.warning(f"Failed to fetch real Google Trends data: {str(e)}. Using mock data instead.")
            raw_data = _generate_mock_google_trends(industry, time_range, keywords)
            is_mock = True
    
    # Create and return the trend source object
    return TrendSource(
        platform="Google Trends",
        raw_data=raw_data,
        timestamp=datetime.utcnow(),
        metadata={
            "time_range": str(trend_depth),
            "is_mock": is_mock,
            "keywords_used": keywords
        }
    )

async def _fetch_viral_trends(
    industry: str, 
    time_range: str,
    keywords: Optional[List[str]] = None
) -> str:
    """
    Fetch viral/trending topics from Google Trends using real-time trending searches.
    
    Args:
        industry: The industry or niche
        time_range: Time range for trends (e.g., "now 7-d")
        keywords: Optional list of specific keywords to focus on
        
    Returns:
        String containing formatted viral trends data
    """
    # Execute pytrends requests in a ThreadPoolExecutor since it's synchronous
    with concurrent.futures.ThreadPoolExecutor() as executor:
        return await asyncio.get_event_loop().run_in_executor(
            executor, _fetch_viral_trends_sync, industry, time_range, keywords
        )

def _fetch_viral_trends_sync(
    industry: str, 
    time_range: str,
    keywords: Optional[List[str]] = None
) -> str:
    """
    Synchronous function to fetch viral trends data.
    
    Args:
        industry: The industry or niche
        time_range: Time range for trends
        keywords: Optional list of specific keywords to focus on
        
    Returns:
        String containing formatted viral trends data
    """
    # Initialize pytrends with minimal parameters to avoid compatibility issues
    pytrends = TrendReq(hl='en-US', tz=0)
    logger.info("Initialized TrendReq client for viral trends")
    
    # Initialize result string
    result = f"Google Trends VIRAL DATA for {industry}"
    if keywords:
        result += f" with focus on {', '.join(keywords)}"
    result += f" over {time_range}:\n\n"
    
    # Track if we've added any data sections
    sections_added = 0
    
    # Try to get trending searches first (most viral content)
    try:
        logger.info("Fetching trending searches (viral content)")
        
        # Get trending searches by country
        countries = ['united_states', 'worldwide']
        trending_added = False
        
        for country in countries:
            try:
                # Get trending searches - these are the most viral content
                trending_searches = pytrends.trending_searches(pn=country)
                
                if not trending_searches.empty:
                    if not trending_added:
                        result += "VIRAL TRENDING SEARCHES:\n"
                        trending_added = True
                    
                    result += f"Top trending searches in {country.replace('_', ' ').title()}:\n"
                    
                    # Filter for industry relevance if possible
                    filtered_trending = []
                    for idx, row in trending_searches.head(10).iterrows():
                        trend = row[0]
                        is_relevant = (
                            industry.lower() in trend.lower() or 
                            any(kw.lower() in trend.lower() for kw in (keywords or []))
                        )
                        if is_relevant:
                            filtered_trending.append((idx+1, trend, "RELEVANT"))
                        elif len(filtered_trending) < 5:  # Add some non-relevant ones if we don't have enough
                            filtered_trending.append((idx+1, trend, ""))
                    
                    # If no relevant trends, just show top 5
                    if not filtered_trending:
                        for idx, row in trending_searches.head(5).iterrows():
                            result += f"{idx+1}. \"{row[0]}\"\n"
                    else:
                        for idx, trend, tag in filtered_trending:
                            result += f"{idx}. \"{trend}\" {tag}\n"
                    
                    result += "\n"
                    sections_added += 1
                    
                    # Only use one country if successful
                    if sections_added > 0:
                        break
                        
            except Exception as e:
                logger.warning(f"Error getting trending searches for {country}: {str(e)}")
                
            # Add delay between country requests
            time.sleep(2)
    
    except Exception as e:
        logger.warning(f"Error getting trending searches: {str(e)}")
    
    # Try to get real-time trending searches (also very viral)
    if sections_added < 2:
        try:
            logger.info("Fetching real-time trending searches")
            time.sleep(2)  # Delay to avoid rate limiting
            
            realtime_trending = pytrends.realtime_trending_searches(pn='US')
            if realtime_trending is not None and not realtime_trending.empty:
                result += "REAL-TIME VIRAL TRENDS:\n"
                
                # Process the real-time trends to find relevant ones
                relevant_trends = []
                for _, row in realtime_trending.head(20).iterrows():
                    title = row.get('title', '')
                    if not title:
                        continue
                        
                    # Check if relevant to industry or keywords
                    is_relevant = (
                        industry.lower() in title.lower() or 
                        any(kw.lower() in title.lower() for kw in (keywords or []))
                    )
                    
                    # Get traffic if available
                    traffic = row.get('traffic', 'N/A')
                    
                    if is_relevant:
                        relevant_trends.append((title, traffic, "HIGHLY RELEVANT"))
                    elif len(relevant_trends) < 8:  # Include some non-relevant ones if we don't have enough
                        relevant_trends.append((title, traffic, ""))
                
                # If no relevant trends found, just show top trends
                if not relevant_trends:
                    for i, (_, row) in enumerate(realtime_trending.head(8).iterrows()):
                        title = row.get('title', f"Trend {i+1}")
                        traffic = row.get('traffic', 'N/A')
                        result += f"{i+1}. \"{title}\" - Traffic: {traffic}\n"
                else:
                    for i, (title, traffic, tag) in enumerate(relevant_trends):
                        result += f"{i+1}. \"{title}\" - Traffic: {traffic} {tag}\n"
                
                result += "\n"
                sections_added += 1
        except Exception as e:
            logger.warning(f"Error getting real-time trending searches: {str(e)}")
    
    # If we didn't get enough viral data, try regular search trends
    if sections_added < 2:
        try:
            logger.info("Fetching standard trends as backup for viral data")
            time.sleep(2)  # Delay to avoid rate limiting
            
            # Create search terms based on industry and keywords
            search_terms = [industry]
            if keywords:
                for keyword in keywords[:1]:  # Just use one keyword to avoid rate limiting
                    search_terms.append(f"{keyword} {industry}")
            
            # Build the payload - fewer terms to avoid rate limiting
            pytrends.build_payload(search_terms[:2], cat=0, timeframe=time_range, geo='US', gprop='')
            
            # Get related queries
            try:
                related_queries = pytrends.related_queries()
                queries_added = False
                
                if related_queries:
                    for term in search_terms[:2]:
                        if term in related_queries and related_queries[term] is not None:
                            # Try rising first (more likely to be viral)
                            if 'rising' in related_queries[term] and related_queries[term]['rising'] is not None:
                                rising_df = related_queries[term]['rising']
                                if not rising_df.empty:
                                    if not queries_added:
                                        result += "RAPIDLY RISING SEARCHES (VIRAL INDICATORS):\n"
                                        queries_added = True
                                    
                                    result += f"Rising searches related to '{term}':\n"
                                    
                                    try:
                                        for i, row in enumerate(rising_df.head(5).to_dict('records')):
                                            query = row.get('query', f"Query {i+1}")
                                            value = row.get('value', 'N/A')
                                            result += f"{i+1}. \"{query}\" - {value}% increase\n"
                                    except Exception as row_err:
                                        logger.warning(f"Error processing row data: {str(row_err)}")
                    
                    if queries_added:
                        result += "\n"
                        sections_added += 1
            except Exception as e:
                logger.warning(f"Error getting related queries for viral data: {str(e)}")
        except Exception as e:
            logger.warning(f"Error getting standard trends as backup for viral data: {str(e)}")
    
    # If we didn't get enough data sections, throw an exception to fall back to the next method
    if sections_added < 1:
        raise ValueError("Insufficient viral trends data retrieved from Google Trends")
    
    return result

async def _fetch_real_google_trends(
    industry: str, 
    time_range: str,
    keywords: Optional[List[str]] = None
) -> str:
    """
    Fetch real Google Trends data using pytrends.
    
    Args:
        industry: The industry or niche
        time_range: Time range for trends (e.g., "now 7-d")
        keywords: Optional list of specific keywords to focus on
        
    Returns:
        String containing formatted Google Trends data
    """
    # Execute pytrends requests in a ThreadPoolExecutor since it's synchronous
    with concurrent.futures.ThreadPoolExecutor() as executor:
        return await asyncio.get_event_loop().run_in_executor(
            executor, _fetch_google_trends_sync, industry, time_range, keywords
        )

def _fetch_google_trends_sync(
    industry: str, 
    time_range: str,
    keywords: Optional[List[str]] = None
) -> str:
    """
    Synchronous function to fetch Google Trends data.
    
    Args:
        industry: The industry or niche
        time_range: Time range for trends
        keywords: Optional list of specific keywords to focus on
        
    Returns:
        String containing formatted Google Trends data
    """
    import time
    
    # Initialize pytrends with compatibility fixes
    # Avoid using retries/backoff parameters which cause compatibility issues
    try:
        pytrends = TrendReq(hl='en-US', tz=0, timeout=(10, 25))
        logger.info("Successfully initialized TrendReq client")
    except Exception as e:
        logger.error(f"Error initializing TrendReq client: {str(e)}")
        # Try with minimal parameters if the first attempt fails
        pytrends = TrendReq(hl='en-US', tz=0)
        logger.info("Initialized TrendReq with minimal parameters")
    
    # Create search queries
    search_terms = []
    
    # Add industry as the base term
    search_terms.append(industry)
    
    # Add keywords if provided
    if keywords:
        for keyword in keywords[:2]:  # Limit to fewer keywords to reduce complexity
            if len(search_terms) < 3:  # Reduce from 5 to 3 to avoid rate limiting
                search_terms.append(f"{keyword} {industry}")
    
    # If we have room for more terms, add some generic industry terms
    while len(search_terms) < 3:  # Reduced from 5 to 3
        additional_terms = [
            f"{industry} trends", 
            f"{industry} news"
        ]
        for term in additional_terms:
            if term not in search_terms and len(search_terms) < 3:
                search_terms.append(term)
    
    # Initialize result string
    result = f"Google Trends data for {industry}"
    if keywords:
        result += f" with focus on {', '.join(keywords)}"
    result += f" over {time_range}:\n\n"
    
    # Track if we've added any data sections
    sections_added = 0
    attempts_remaining = 3
    
    while sections_added < 2 and attempts_remaining > 0:
        try:
            # Build the payload
            logger.info(f"Building payload for terms: {search_terms}")
            pytrends.build_payload(search_terms, cat=0, timeframe=time_range, geo='', gprop='')
            
            # Get interest over time
            try:
                # Add delay before first request to avoid immediate rate limiting
                time.sleep(1)
                
                interest_over_time_df = pytrends.interest_over_time()
                if not interest_over_time_df.empty:
                    result += "INTEREST OVER TIME:\n"
                    # Calculate averages for each term
                    for term in search_terms:
                        if term in interest_over_time_df.columns:
                            avg_interest = interest_over_time_df[term].mean()
                            result += f"{term}: {avg_interest:.1f}/100\n"
                    result += "\n"
                    sections_added += 1
            except Exception as e:
                logger.warning(f"Error getting interest over time: {str(e)}")
            
            # Add significant delay between requests
            time.sleep(3)
            
            # Get related topics
            try:
                related_topics = pytrends.related_topics()
                topics_added = False
                
                if related_topics:
                    for term in search_terms:
                        if term in related_topics and 'rising' in related_topics[term]:
                            rising_df = related_topics[term]['rising']
                            if not rising_df.empty:
                                if not topics_added:
                                    result += "RELATED TOPICS:\n"
                                    topics_added = True
                                
                                result += f"Rising topics related to '{term}':\n"
                                for i, (_, row) in enumerate(rising_df.head(3).iterrows()):  # Reduced from 5 to 3
                                    result += f"{i+1}. {row['topic_title']} - {row['value']}% increase\n"
                    
                    if topics_added:
                        result += "\n"
                        sections_added += 1
            except Exception as e:
                logger.warning(f"Error getting related topics: {str(e)}")
            
            # Add significant delay between requests
            time.sleep(3)
            
            # Get related queries - wrap in try/except for list index error
            try:
                related_queries = pytrends.related_queries()
                queries_added = False
                
                if related_queries:
                    for term in search_terms:
                        # Check each level carefully to avoid index errors
                        if term in related_queries and related_queries[term] is not None:
                            if 'rising' in related_queries[term] and related_queries[term]['rising'] is not None:
                                rising_df = related_queries[term]['rising']
                                if not rising_df.empty:
                                    if not queries_added:
                                        result += "RELATED QUERIES:\n"
                                        queries_added = True
                                    
                                    result += f"Rising queries related to '{term}':\n"
                                    # Use safer iteration approach
                                    try:
                                        for i, row in enumerate(rising_df.head(3).to_dict('records')):
                                            query = row.get('query', f"Query {i+1}")
                                            value = row.get('value', 'N/A')
                                            result += f"{i+1}. \"{query}\" - {value}% increase\n"
                                    except Exception as row_err:
                                        logger.warning(f"Error processing row data: {str(row_err)}")
                    
                    if queries_added:
                        result += "\n"
                        sections_added += 1
            except IndexError as e:
                logger.warning(f"Error getting related queries (index error): {str(e)}")
            except Exception as e:
                logger.warning(f"Error getting related queries: {str(e)}")
            
            # Add significant delay between requests
            time.sleep(3)
            
            # Get geographic interest - only try if we need more sections
            if sections_added < 2:
                try:
                    interest_by_region = pytrends.interest_by_region(resolution='COUNTRY', inc_low_vol=True)
                    if not interest_by_region.empty:
                        result += "GEOGRAPHIC INTEREST (Top 5 Countries):\n"
                        for term in search_terms[:1]:  # Just use the main term to avoid too much data
                            if term in interest_by_region.columns:
                                top_regions = interest_by_region[term].sort_values(ascending=False).head(5)
                                for country, value in top_regions.items():
                                    result += f"{country}: {value}/100\n"
                        sections_added += 1
                except Exception as e:
                    logger.warning(f"Error getting geographic interest: {str(e)}")
            
            # If we got at least 2 sections, break out of the loop
            if sections_added >= 2:
                break
                
        except Exception as e:
            logger.warning(f"Error in Google Trends API request: {str(e)}")
            
        # Reduce attempt count and sleep before retry
        attempts_remaining -= 1
        if attempts_remaining > 0:
            logger.info(f"Retrying Google Trends request ({attempts_remaining} attempts left)")
            time.sleep(5)  # Wait longer before retry
    
    # If we didn't get enough data sections, throw an exception to fall back to mock data
    if sections_added < 2:
        raise ValueError("Insufficient data retrieved from Google Trends")
    
    return result

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