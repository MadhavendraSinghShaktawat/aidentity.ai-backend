"""
YouTube Source

This module fetches trending topics from YouTube using the YouTube Data API.
It focuses on identifying viral videos and extracting meaningful trends based on
engagement metrics, video metadata, and content analysis.
"""
import logging
import asyncio
import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import re
import concurrent.futures
import time
from urllib.parse import quote

import aiohttp
from fastapi import HTTPException
import html

from ..schemas import TrendSource, TrendDepth

logger = logging.getLogger(__name__)

# Get API key from environment variables
# First try YouTube-specific key, then fall back to generic Google API key
YOUTUBE_API_KEY = os.environ.get("YT_GOOGLE_KEY", "") or os.environ.get("GOOGLE_API_KEY", "")

# Base URL for YouTube Data API
YOUTUBE_API_BASE_URL = "https://www.googleapis.com/youtube/v3"

async def fetch_youtube_trends(
    industry: str, 
    trend_depth: TrendDepth,
    keywords: Optional[List[str]] = None
) -> TrendSource:
    """
    Fetch trending videos and topics from YouTube based on industry and time range.
    
    Args:
        industry: The industry or niche to analyze
        trend_depth: How far back to analyze trends
        keywords: Optional list of specific keywords to focus on
        
    Returns:
        A TrendSource object with YouTube trend data
    """
    logger.info(f"Fetching YouTube trends for {industry} with depth {trend_depth}")
    
    # Determine the published after date based on trend depth
    published_after = _get_published_date(trend_depth)
    
    try:
        # Check if API key is available
        if not YOUTUBE_API_KEY:
            logger.warning("YouTube API key not found in environment variables. Using mock data.")
            raise ValueError("YouTube API key not found")
        
        # Construct search terms
        search_terms = [industry]
        if keywords:
            for keyword in keywords:
                search_terms.append(f"{keyword} {industry}")
        
        # Fetch YouTube trends data
        raw_data = await _fetch_real_youtube_trends(search_terms, published_after)
        is_mock = False
        logger.info("Successfully fetched YouTube trends data")
    except Exception as e:
        logger.warning(f"Failed to fetch YouTube trends: {str(e)}. Using mock data instead.")
        raw_data = _generate_mock_youtube_trends(industry, trend_depth, keywords)
        is_mock = True
    
    # Create and return the trend source object
    return TrendSource(
        platform="YouTube",
        raw_data=raw_data,
        timestamp=datetime.utcnow(),
        metadata={
            "time_range": str(trend_depth),
            "is_mock": is_mock,
            "keywords_used": keywords
        }
    )

def _get_published_date(trend_depth: TrendDepth) -> str:
    """
    Convert trend depth to ISO 8601 formatted date string for YouTube API.
    
    Args:
        trend_depth: How far back to analyze trends
        
    Returns:
        ISO 8601 formatted date string
    """
    now = datetime.utcnow()
    
    # Get the trend depth string to handle different enum naming conventions
    trend_depth_str = str(trend_depth)
    
    if "DAY" in trend_depth_str or "day" in trend_depth_str:
        date = now - timedelta(days=1)
    elif "WEEK" in trend_depth_str or "week" in trend_depth_str:
        date = now - timedelta(days=7)
    elif "MONTH" in trend_depth_str or "month" in trend_depth_str:
        date = now - timedelta(days=30)
    else:
        logger.warning(f"Unknown trend depth: {trend_depth}, defaulting to 1 day")
        date = now - timedelta(days=1)  # Default to 1 day
    
    # Format as RFC 3339 timestamp
    return date.strftime('%Y-%m-%dT%H:%M:%SZ')

async def _fetch_real_youtube_trends(
    search_terms: List[str],
    published_after: str
) -> str:
    """
    Fetch real YouTube trends data using the YouTube Data API.
    
    Args:
        search_terms: List of search terms to fetch trends for
        published_after: Date filter for videos published after this date
        
    Returns:
        Formatted string with YouTube trends data
    """
    # Create a session for all requests
    async with aiohttp.ClientSession() as session:
        # Fetch trends for each search term concurrently
        tasks = []
        for term in search_terms[:3]:  # Limit to 3 terms to avoid rate limiting
            tasks.append(_fetch_term_trends(session, term, published_after))
        
        # Gather results
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results, handling any exceptions
        valid_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"Failed to fetch trends for a search term: {str(result)}")
            else:
                valid_results.append(result)
        
        if not valid_results:
            raise ValueError("Failed to fetch trends for any search term")
        
        # Combine results and format output
        return _format_youtube_results(valid_results, search_terms)

async def _fetch_term_trends(
    session: aiohttp.ClientSession,
    search_term: str,
    published_after: str
) -> Dict[str, Any]:
    """
    Fetch trending videos for a specific search term.
    
    Args:
        session: aiohttp client session
        search_term: Term to search for
        published_after: Date filter for videos
        
    Returns:
        Dictionary with search results and metadata
    """
    logger.info(f"Searching YouTube for: {search_term}")
    
    # Encode the search term for URL
    encoded_term = quote(search_term)
    
    # Build the search URL with parameters
    search_url = (
        f"{YOUTUBE_API_BASE_URL}/search"
        f"?part=snippet"
        f"&q={encoded_term}"
        f"&type=video"
        f"&order=viewCount"  # Sort by view count to find viral content
        f"&publishedAfter={published_after}"
        f"&relevanceLanguage=en"
        f"&maxResults=15"  # Ask for 15 videos
        f"&key={YOUTUBE_API_KEY}"
    )
    
    try:
        # Make the API request
        async with session.get(search_url) as response:
            if response.status != 200:
                error_text = await response.text()
                logger.error(f"YouTube API error: {error_text}")
                raise ValueError(f"YouTube API returned status code {response.status}")
            
            search_data = await response.json()
            
            # Check if we got valid results
            if "items" not in search_data or not search_data["items"]:
                logger.warning(f"No videos found for search term: {search_term}")
                return {"search_term": search_term, "items": [], "error": "No videos found"}
            
            # Extract video IDs for additional metadata
            video_ids = [item["id"]["videoId"] for item in search_data["items"]]
            
            # Get engagement metrics for these videos
            video_data = await _get_video_details(session, video_ids)
            
            # Combine search results with video details
            result = {
                "search_term": search_term,
                "items": _merge_video_data(search_data["items"], video_data),
                "total_results": search_data.get("pageInfo", {}).get("totalResults", 0)
            }
            
            return result
    except Exception as e:
        logger.error(f"Error fetching YouTube trends for {search_term}: {str(e)}")
        raise e

async def _get_video_details(
    session: aiohttp.ClientSession,
    video_ids: List[str]
) -> Dict[str, Any]:
    """
    Get detailed information about specific videos.
    
    Args:
        session: aiohttp client session
        video_ids: List of video IDs to get details for
        
    Returns:
        Dictionary mapping video IDs to their details
    """
    # Join the video IDs with commas
    ids_str = ",".join(video_ids)
    
    # Build the videos URL with parameters
    videos_url = (
        f"{YOUTUBE_API_BASE_URL}/videos"
        f"?part=statistics,contentDetails"
        f"&id={ids_str}"
        f"&key={YOUTUBE_API_KEY}"
    )
    
    try:
        # Make the API request
        async with session.get(videos_url) as response:
            if response.status != 200:
                error_text = await response.text()
                logger.error(f"YouTube API error (video details): {error_text}")
                raise ValueError(f"YouTube API returned status code {response.status}")
            
            videos_data = await response.json()
            
            # Create a dictionary mapping video IDs to their details
            video_details = {}
            for item in videos_data.get("items", []):
                video_details[item["id"]] = {
                    "statistics": item.get("statistics", {}),
                    "contentDetails": item.get("contentDetails", {})
                }
            
            return video_details
    except Exception as e:
        logger.error(f"Error fetching video details: {str(e)}")
        raise e

def _merge_video_data(
    search_items: List[Dict[str, Any]],
    video_details: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Merge search results with video details.
    
    Args:
        search_items: List of search result items
        video_details: Dictionary mapping video IDs to their details
        
    Returns:
        List of merged video data
    """
    merged_items = []
    
    for item in search_items:
        video_id = item["id"]["videoId"]
        details = video_details.get(video_id, {})
        
        # Extract view count and other statistics
        statistics = details.get("statistics", {})
        view_count = int(statistics.get("viewCount", 0))
        like_count = int(statistics.get("likeCount", 0))
        comment_count = int(statistics.get("commentCount", 0))
        
        # Extract duration
        content_details = details.get("contentDetails", {})
        duration = content_details.get("duration", "")
        
        # Calculate engagement ratio (likes + comments per view)
        # This helps identify truly engaging content, not just view bait
        engagement_ratio = 0
        if view_count > 0:
            engagement_ratio = (like_count + comment_count) / view_count
        
        # Calculate a viral score based on views and engagement
        # Higher score means more viral potential
        viral_score = min(100, (view_count / 10000) * (engagement_ratio * 1000))
        
        # Calculate trending score for recent content (values freshness)
        published_at = item["snippet"]["publishedAt"]
        published_time = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")
        days_ago = (datetime.utcnow() - published_time).days
        recency_factor = max(0.2, 1 - (days_ago / 14))  # Newer content gets higher factor
        trending_score = viral_score * recency_factor
        
        # Add calculated fields to the item
        merged_item = {
            **item,
            "statistics": statistics,
            "contentDetails": content_details,
            "metrics": {
                "viewCount": view_count,
                "likeCount": like_count,
                "commentCount": comment_count,
                "engagementRatio": engagement_ratio,
                "viralScore": viral_score,
                "trendingScore": trending_score,
                "daysAgo": days_ago
            }
        }
        
        merged_items.append(merged_item)
    
    # Sort by trending score (descending)
    merged_items.sort(key=lambda x: x["metrics"]["trendingScore"], reverse=True)
    
    return merged_items

def _format_youtube_results(
    results: List[Dict[str, Any]],
    search_terms: List[str]
) -> str:
    """
    Format YouTube API results into a readable string.
    
    Args:
        results: List of search results
        search_terms: List of search terms used
        
    Returns:
        Formatted string with YouTube trends data
    """
    # Start with a header
    search_terms_str = ", ".join(search_terms)
    output = f"YouTube trending videos for search terms: {search_terms_str}\n\n"
    
    # Process each search term's results
    for result in results:
        search_term = result["search_term"]
        items = result["items"]
        
        if not items:
            output += f"No trending videos found for: {search_term}\n\n"
            continue
        
        # Add section header for this search term
        output += f"TRENDING VIDEOS FOR: {search_term.upper()}\n"
        
        # Add video details
        for i, item in enumerate(items[:10]):  # Limit to top 10 videos
            try:
                # Extract basic information
                title = html.unescape(item["snippet"]["title"])
                channel = html.unescape(item["snippet"]["channelTitle"])
                video_id = item["id"]["videoId"]
                view_count = item["metrics"]["viewCount"]
                like_count = item["metrics"]["likeCount"]
                comment_count = item["metrics"]["commentCount"]
                viral_score = item["metrics"]["viralScore"]
                days_ago = item["metrics"]["daysAgo"]
                
                # Classify virality level
                virality = "TRENDING"
                if viral_score > 80:
                    virality = "MEGA VIRAL"
                elif viral_score > 50:
                    virality = "HIGHLY VIRAL"
                elif viral_score > 20:
                    virality = "VIRAL"
                
                # Format the video entry
                published_str = f"{days_ago} days ago" if days_ago != 1 else "1 day ago"
                
                output += (
                    f"{i+1}. [{virality}] \"{title}\"\n"
                    f"   Channel: {channel} | {published_str}\n"
                    f"   Views: {view_count:,} | Likes: {like_count:,} | Comments: {comment_count:,}\n"
                    f"   Viral Score: {viral_score:.1f}/100\n"
                    f"   URL: https://www.youtube.com/watch?v={video_id}\n\n"
                )
            except Exception as e:
                logger.warning(f"Error formatting video item: {str(e)}")
                continue
        
        # Extract common keywords from titles
        keywords = _extract_common_keywords(items)
        if keywords:
            output += "COMMON KEYWORDS IN TRENDING VIDEOS:\n"
            output += ", ".join(keywords) + "\n\n"
        
        # Extract emerging topics from video titles and descriptions
        topics = _extract_topics(items)
        if topics:
            output += "EMERGING TOPICS IN TRENDING VIDEOS:\n"
            for topic, count in topics:
                output += f"- {topic} (found in {count} videos)\n"
            output += "\n"
        
        # Add engagement insights
        total_views = sum(item["metrics"]["viewCount"] for item in items)
        average_engagement = sum(item["metrics"]["engagementRatio"] for item in items) / len(items)
        output += f"ENGAGEMENT INSIGHTS FOR {search_term.upper()}:\n"
        output += f"Total views across trending videos: {total_views:,}\n"
        output += f"Average engagement ratio: {average_engagement:.6f}\n\n"
    
    # Add overall trend analysis
    output += "OVERALL YOUTUBE TREND ANALYSIS:\n"
    
    # Identify the most viral videos across all searches
    all_videos = []
    for result in results:
        all_videos.extend(result["items"])
    
    # Sort by viral score
    all_videos.sort(key=lambda x: x["metrics"]["viralScore"], reverse=True)
    
    # Extract top 5 viral videos
    if all_videos:
        output += "TOP 5 MOST VIRAL VIDEOS OVERALL:\n"
        for i, video in enumerate(all_videos[:5]):
            title = html.unescape(video["snippet"]["title"])
            channel = html.unescape(video["snippet"]["channelTitle"])
            viral_score = video["metrics"]["viralScore"]
            output += f"{i+1}. \"{title}\" by {channel} - Viral Score: {viral_score:.1f}/100\n"
    
    # Add cross-search-term insights
    all_keywords = _extract_common_keywords(all_videos)
    if all_keywords:
        output += "\nTOP KEYWORDS ACROSS ALL SEARCHES:\n"
        output += ", ".join(all_keywords[:10]) + "\n"
    
    return output

def _extract_common_keywords(items: List[Dict[str, Any]]) -> List[str]:
    """
    Extract common keywords from video titles and descriptions.
    
    Args:
        items: List of video items
        
    Returns:
        List of common keywords sorted by frequency (descending)
    """
    # Combine all titles and descriptions
    text = ""
    for item in items:
        text += item["snippet"]["title"] + " "
        text += item["snippet"]["description"] + " "
    
    # Convert to lowercase and remove special characters
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    
    # Split into words
    words = text.split()
    
    # Count word frequencies
    word_counts = {}
    for word in words:
        if len(word) > 3 and word not in ["this", "that", "with", "from", "have", "what", "your", "there", "about"]:
            word_counts[word] = word_counts.get(word, 0) + 1
    
    # Sort by frequency (descending)
    sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
    
    # Return the top keywords
    return [word for word, count in sorted_words[:15]]

def _extract_topics(items: List[Dict[str, Any]]) -> List[Tuple[str, int]]:
    """
    Extract emerging topics from video titles and descriptions.
    
    Args:
        items: List of video items
        
    Returns:
        List of (topic, count) tuples sorted by count (descending)
    """
    # Combine all titles
    titles = [item["snippet"]["title"].lower() for item in items]
    
    # Define patterns to look for (e.g., "how to", "why", "tutorial", etc.)
    patterns = {
        r'how\s+to\s+(\w+(?:\s+\w+){0,5})': "How to",
        r'why\s+(\w+(?:\s+\w+){0,5})': "Why",
        r'(\w+(?:\s+\w+){0,2})\s+tutorial': "Tutorial",
        r'(\w+(?:\s+\w+){0,2})\s+guide': "Guide",
        r'(\w+(?:\s+\w+){0,2})\s+tips': "Tips",
        r'(\w+(?:\s+\w+){0,2})\s+review': "Review",
        r'(\w+(?:\s+\w+){0,2})\s+vs': "Comparison",
        r'best\s+(\w+(?:\s+\w+){0,3})': "Best",
        r'new\s+(\w+(?:\s+\w+){0,3})': "New",
    }
    
    # Extract topics using patterns
    topics = {}
    for title in titles:
        for pattern, topic_type in patterns.items():
            matches = re.finditer(pattern, title)
            for match in matches:
                topic_text = match.group(1).strip()
                if len(topic_text) > 3:
                    full_topic = f"{topic_type}: {topic_text}"
                    topics[full_topic] = topics.get(full_topic, 0) + 1
    
    # Sort by count (descending)
    sorted_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)
    
    # Return the top topics
    return sorted_topics[:10]

def _generate_mock_youtube_trends(
    industry: str, 
    trend_depth: TrendDepth,
    keywords: Optional[List[str]] = None
) -> str:
    """
    Generate mock YouTube trends data.
    
    Args:
        industry: The industry or niche
        trend_depth: Time range for trends
        keywords: Optional list of specific keywords to focus on
        
    Returns:
        String containing mock YouTube trends data
    """
    keyword_str = ""
    if keywords:
        keyword_str = f" with focus on {', '.join(keywords)}"
    
    result = f"YouTube trending videos for {industry}{keyword_str} (MOCK DATA):\n\n"
    
    # Define mock trending videos for different industries
    industry_videos = {
        "tech": [
            {
                "title": "I Spent 30 Days Testing ChatGPT 4 And Here's What Happened",
                "channel": "Tech Insights",
                "views": 2500000,
                "likes": 195000,
                "comments": 15700,
                "days_ago": 5,
                "viral_score": 85.3
            },
            {
                "title": "This AI Tool Will Replace Your Job By 2025",
                "channel": "Future Tech Now",
                "views": 1800000,
                "likes": 145000,
                "comments": 22000,
                "days_ago": 3,
                "viral_score": 92.1
            },
            {
                "title": "Apple's Secret Project LEAKED - What They Don't Want You To Know",
                "channel": "Tech Leaks",
                "views": 3200000,
                "likes": 255000,
                "comments": 32000,
                "days_ago": 2,
                "viral_score": 98.4
            }
        ],
        "fitness": [
            {
                "title": "The Only 3 Exercises You Need For A Complete Physique",
                "channel": "Fitness Master",
                "views": 1700000,
                "likes": 120000,
                "comments": 8500,
                "days_ago": 6,
                "viral_score": 77.6
            },
            {
                "title": "I Tried The Rock's Diet & Workout For 30 Days",
                "channel": "Fitness Challenge",
                "views": 4500000,
                "likes": 375000,
                "comments": 22000,
                "days_ago": 7,
                "viral_score": 88.9
            },
            {
                "title": "This Breathing Technique Will Change Your Workout Forever",
                "channel": "Breath & Strength",
                "views": 2100000,
                "likes": 185000,
                "comments": 12000,
                "days_ago": 4,
                "viral_score": 82.7
            }
        ],
        "business": [
            {
                "title": "How I Built a 7-Figure Business Working 4 Hours A Week",
                "channel": "Entrepreneur Mindset",
                "views": 1250000,
                "likes": 95000,
                "comments": 8700,
                "days_ago": 8,
                "viral_score": 76.3
            },
            {
                "title": "5 Passive Income Streams That Actually Work In 2024",
                "channel": "Financial Freedom",
                "views": 3600000,
                "likes": 285000,
                "comments": 19000,
                "days_ago": 5,
                "viral_score": 87.2
            },
            {
                "title": "How To Start An Online Business With Zero Investment",
                "channel": "Digital Entrepreneurs",
                "views": 2200000,
                "likes": 178000,
                "comments": 15400,
                "days_ago": 3,
                "viral_score": 84.5
            }
        ]
    }
    
    # Default videos if industry not found
    default_videos = [
        {
            "title": "10 Things You Should Know About 2024 Trends",
            "channel": "Trend Watch",
            "views": 1850000,
            "likes": 145000,
            "comments": 12500,
            "days_ago": 6,
            "viral_score": 79.3
        },
        {
            "title": "The Truth About What's Happening In The World Right Now",
            "channel": "Global Insights",
            "views": 3750000,
            "likes": 320000,
            "comments": 28000,
            "days_ago": 4,
            "viral_score": 93.8
        },
        {
            "title": "I Tried The Viral TikTok Trend And It Changed Everything",
            "channel": "Trend Testing",
            "views": 2900000,
            "likes": 265000,
            "comments": 22000,
            "days_ago": 2,
            "viral_score": 91.2
        }
    ]
    
    # Get videos for the specific industry or use default
    normalized_industry = industry.lower()
    videos = []
    
    for ind, ind_videos in industry_videos.items():
        if ind in normalized_industry or normalized_industry in ind:
            videos = ind_videos
            break
    
    if not videos:
        videos = default_videos
    
    # If keywords provided, add keyword-specific videos
    if keywords:
        for keyword in keywords[:2]:
            videos.insert(0, {
                "title": f"Why {keyword} Is Changing The {industry} Industry Forever",
                "channel": f"{industry.title()} Insights",
                "views": 2200000 + (hash(keyword) % 1000000),
                "likes": 185000 + (hash(keyword) % 50000),
                "comments": 15000 + (hash(keyword) % 5000),
                "days_ago": hash(keyword) % 7 + 1,
                "viral_score": 80 + (hash(keyword) % 15)
            })
    
    # Add trending videos section
    result += "TRENDING VIDEOS:\n"
    for i, video in enumerate(videos):
        virality = "TRENDING"
        if video["viral_score"] > 90:
            virality = "MEGA VIRAL"
        elif video["viral_score"] > 80:
            virality = "HIGHLY VIRAL"
        elif video["viral_score"] > 70:
            virality = "VIRAL"
            
        result += (
            f"{i+1}. [{virality}] \"{video['title']}\"\n"
            f"   Channel: {video['channel']} | {video['days_ago']} days ago\n"
            f"   Views: {video['views']:,} | Likes: {video['likes']:,} | Comments: {video['comments']:,}\n"
            f"   Viral Score: {video['viral_score']:.1f}/100\n"
            f"   URL: https://www.youtube.com/watch?v=mockid{i}\n\n"
        )
    
    # Add common keywords
    result += "COMMON KEYWORDS IN TRENDING VIDEOS:\n"
    mock_keywords = [
        industry, "trending", "viral", "2024", "new", "best", 
        "how to", "tutorial", "review", "guide", "tips"
    ]
    if keywords:
        mock_keywords.extend(keywords)
    result += ", ".join(mock_keywords) + "\n\n"
    
    # Add emerging topics
    result += "EMERGING TOPICS IN TRENDING VIDEOS:\n"
    mock_topics = [
        ("How to: master " + industry, 5),
        ("Tutorial: best practices for " + industry, 4),
        ("Review: top " + industry + " tools", 3),
        ("Tips: improving your " + industry + " skills", 3),
    ]
    for topic, count in mock_topics:
        result += f"- {topic} (found in {count} videos)\n"
    result += "\n"
    
    # Add engagement insights
    result += f"ENGAGEMENT INSIGHTS FOR {industry.upper()}:\n"
    result += f"Total views across trending videos: {sum(v['views'] for v in videos):,}\n"
    result += f"Average engagement ratio: {0.000125:.6f}\n\n"
    
    # Add overall trend analysis
    result += "OVERALL YOUTUBE TREND ANALYSIS:\n"
    result += "TOP 5 MOST VIRAL VIDEOS OVERALL:\n"
    for i, video in enumerate(sorted(videos, key=lambda x: x["viral_score"], reverse=True)[:5]):
        title = video["title"]
        channel = video["channel"]
        viral_score = video["viral_score"]
        result += f"{i+1}. \"{title}\" by {channel} - Viral Score: {viral_score:.1f}/100\n"
    
    result += "\nTOP KEYWORDS ACROSS ALL SEARCHES:\n"
    result += "viral, trending, how to, tutorial, review, best, new, 2024, guide, tips\n"
    
    return result 