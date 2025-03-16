"""
Reddit Trends Source

This module fetches trending topics from Reddit.
"""
import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

import aiohttp
from fastapi import HTTPException

from ..schemas import TrendSource, TrendDepth

logger = logging.getLogger(__name__)

async def fetch_reddit_trends(
    industry: str, 
    trend_depth: TrendDepth,
    keywords: Optional[List[str]] = None
) -> TrendSource:
    """
    Fetch trending topics from Reddit based on industry and time range.
    
    Args:
        industry: The industry or niche to analyze
        trend_depth: How far back to analyze trends
        keywords: Optional list of specific keywords to focus on
        
    Returns:
        A TrendSource object with the raw Reddit data
    """
    # For now, we'll use mock data until Reddit API is set up
    keyword_str = f" with keywords {', '.join(keywords)}" if keywords else ""
    logger.info(f"Using mock Reddit data for {industry}{keyword_str} with depth {trend_depth}")
    
    # Set time filter based on trend depth
    time_filter = "day"
    if trend_depth == "Past Week":
        time_filter = "week"
    elif trend_depth == "Monthly":
        time_filter = "month"
    
    # Get relevant subreddits
    subreddits = await _get_relevant_subreddits(industry, keywords)
    
    # Generate mock data based on industry and subreddits
    mock_data = _generate_mock_reddit_data(industry, subreddits, time_filter, keywords)
    
    # Create and return the trend source object
    return TrendSource(
        platform="Reddit",
        raw_data=mock_data,
        timestamp=datetime.utcnow(),
        metadata={
            "subreddits": subreddits,
            "time_range": str(trend_depth),
            "is_mock": True,  # Flag to indicate this is mock data
            "keywords_used": keywords
        }
    )

async def _get_relevant_subreddits(industry: str, keywords: Optional[List[str]] = None) -> List[str]:
    """
    Determine relevant subreddits based on the industry and keywords.
    
    Args:
        industry: The industry or niche
        keywords: Optional list of specific keywords
        
    Returns:
        List of relevant subreddit names
    """
    # This is a simplified version - in a real implementation, you'd have a more
    # comprehensive mapping or use a search API to find relevant subreddits
    industry_map = {
        "tech": ["technology", "programming", "webdev", "artificial", "machinelearning"],
        "fitness": ["fitness", "bodybuilding", "running", "yoga", "nutrition"],
        "business": ["entrepreneur", "startups", "smallbusiness", "marketing", "sales"],
        "fashion": ["malefashionadvice", "femalefashionadvice", "streetwear", "sneakers"],
        "gaming": ["gaming", "pcgaming", "ps4", "xboxone", "nintendoswitch"],
        "health": ["health", "nutrition", "medicine", "psychology", "meditation"],
        "food": ["food", "cooking", "recipes", "mealprep", "foodhacks"],
        "travel": ["travel", "backpacking", "solotravel", "roadtrip", "camping"],
        "entertainment": ["movies", "television", "music", "books", "anime"]
    }
    
    # Special keyword-related subreddits
    keyword_map = {
        "ai": ["artificial", "MachineLearning", "deeplearning", "singularity"],
        "crypto": ["CryptoCurrency", "Bitcoin", "ethereum", "CryptoMarkets"],
        "nft": ["NFT", "NFTsMarketplace", "NFTart"],
        "metaverse": ["metaverse", "VirtualReality", "oculus"],
        "blockchain": ["BlockChain", "CryptoTechnology", "ethereum"],
        "sustainability": ["sustainability", "ClimateActionPlan", "ZeroWaste"],
        "remote work": ["digitalnomad", "WorkOnline", "remotework"],
        "mental health": ["mentalhealth", "depression", "Anxiety", "selfimprovement"],
        "startup": ["startups", "Entrepreneur", "SideProject", "smallbusiness"],
    }
    
    # Normalize the industry name
    normalized_industry = industry.lower()
    
    # Get matching subreddits from industry map
    selected_subreddits = []
    for key, subreddits in industry_map.items():
        if key in normalized_industry or normalized_industry in key:
            selected_subreddits.extend(subreddits)
    
    # If keywords provided, add keyword-specific subreddits
    if keywords:
        for keyword in keywords:
            normalized_keyword = keyword.lower()
            # Add direct keyword as subreddit if it might exist
            if len(normalized_keyword) > 3 and ' ' not in normalized_keyword:
                selected_subreddits.append(normalized_keyword)
            
            # Check keyword map
            for key, subreddits in keyword_map.items():
                if normalized_keyword in key or key in normalized_keyword:
                    selected_subreddits.extend(subreddits)
    
    # If no match, add the industry as a subreddit and some general ones
    if not selected_subreddits:
        selected_subreddits = [normalized_industry, "popular", "all", "trending"]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_subreddits = [x for x in selected_subreddits if not (x in seen or seen.add(x))]
    
    return unique_subreddits

def _generate_mock_reddit_data(
    industry: str, 
    subreddits: List[str], 
    time_filter: str, 
    keywords: Optional[List[str]] = None
) -> str:
    """
    Generate mock Reddit data for development purposes.
    
    Args:
        industry: The industry or niche
        subreddits: List of relevant subreddits
        time_filter: Time filter (day, week, month)
        keywords: Optional list of specific keywords to focus on
        
    Returns:
        String containing mock Reddit data
    """
    result = f"Reddit trending topics for {industry}"
    if keywords:
        result += f" with focus on: {', '.join(keywords)}"
    result += f":\n\n"
    
    # Get current trending topics - these would normally come from real API
    current_trends = [
        "AI image generation tools",
        "Open source LLM models",
        "Data privacy concerns",
        "Rust programming language",
        "Cloud computing cost optimization",
        "Automation and job market impacts",
        "Quantum computing breakthroughs",
        "Web3 development",
        "Remote work tools",
        "Tech industry layoffs",
        "AR/VR development",
        "Sustainable tech initiatives",
        "No-code/low-code platforms"
    ]
    
    for i, subreddit in enumerate(subreddits[:3]):  # Limit to 3 subreddits
        result += f"r/{subreddit} - Top trending discussions ({time_filter}):\n"
        
        # Generate posts - if keywords provided, make some posts directly reference them
        posts = []
        
        # Add some keyword-focused posts if keywords are provided
        if keywords and i == 0:  # For the first subreddit, add more keyword-focused content
            for j, keyword in enumerate(keywords[:3]):  # Use up to 3 keywords
                posts.append({
                    "title": f"Breaking: Major developments in {keyword} for {industry} sector",
                    "upvotes": 8200 - (j * 100),
                    "comments": 743 - (j * 30),
                    "keyword_relevance": "high"
                })
                posts.append({
                    "title": f"What everyone is getting wrong about {keyword} in 2024",
                    "upvotes": 6500 - (j * 100),
                    "comments": 892 - (j * 20),
                    "keyword_relevance": "high"
                })
        
        # Add some general trending posts relevant to the industry
        general_posts = [
            {
                "title": f"Latest developments in {industry} technology",
                "upvotes": 5200 - (i * 200),
                "comments": 423 - (i * 30)
            },
            {
                "title": f"How {industry} is changing in 2024", 
                "upvotes": 3800 - (i * 150),
                "comments": 312 - (i * 25)
            },
            {
                "title": f"{industry} experts share insights on future trends",
                "upvotes": 2900 - (i * 100),
                "comments": 187 - (i * 20)
            }
        ]
        
        # Add some current trending topics
        if i == 0:
            # Select 2 random trending topics relevant to the industry
            import random
            random.shuffle(current_trends)
            for trend in current_trends[:2]:
                general_posts.append({
                    "title": f"[Trending] {trend}: Implications for {industry}",
                    "upvotes": random.randint(7000, 12000),
                    "comments": random.randint(500, 1200),
                    "trending": True
                })
        
        # Combine and sort posts by upvotes
        posts.extend(general_posts)
        posts.sort(key=lambda x: x.get("upvotes", 0), reverse=True)
        
        # Add posts to the result
        for j, post in enumerate(posts[:5]):  # Take top 5 posts
            is_trending = post.get("trending", False)
            trending_tag = "[TRENDING] " if is_trending else ""
            high_relevance = post.get("keyword_relevance", "") == "high"
            relevance_tag = "[HIGHLY RELEVANT] " if high_relevance else ""
            
            result += f"{j+1}. {trending_tag}{relevance_tag}\"{post['title']}\" - {post['upvotes']} upvotes, {post['comments']} comments\n"
        
        # Add common keywords
        result += f"\nCommon keywords in r/{subreddit}: "
        common_keywords = ["innovation", "technology", "growth", "challenges", "future", "development"]
        
        # Add user's keywords to the common keywords if provided
        if keywords:
            common_keywords.extend(keywords)
        
        result += ", ".join(common_keywords) + "\n\n"
    
    # Add some meta information
    result += f"Total trending posts for {industry}: {len(subreddits) * 5}\n"
    result += f"Most active time: {['morning', 'afternoon', 'evening'][len(industry) % 3]}\n"
    result += f"Demographics: {'tech-savvy professionals' if 'tech' in industry.lower() else 'mixed audience'}\n"
    
    if keywords:
        result += f"\nKEYWORD ANALYSIS:\n"
        for keyword in keywords:
            result += f"- \"{keyword}\": Increasing popularity, showing in ~{len(subreddits) * 3 + (len(keyword) % 10)} posts this {time_filter}\n"
    
    return result

async def _fetch_subreddit_top_posts(
    session: aiohttp.ClientSession, 
    subreddit: str, 
    time_filter: str
) -> List[Dict[str, Any]]:
    """
    Fetch top posts from a specific subreddit.
    
    Args:
        session: aiohttp client session
        subreddit: Name of the subreddit
        time_filter: Time filter (day, week, month)
        
    Returns:
        List of posts with their data
    """
    # In a real implementation, you would use Reddit's API with proper authentication
    # This is a mock implementation for demonstration purposes
    url = f"https://www.reddit.com/r/{subreddit}/top.json"
    params = {
        "t": time_filter,
        "limit": 10
    }
    
    try:
        # Simulate API request - in a real implementation, this would be an actual API call
        # with proper error handling and rate limiting
        await asyncio.sleep(0.5)  # Simulate network delay
        
        # Mock response data
        posts = []
        for i in range(5):  # Simulate 5 posts per subreddit
            posts.append({
                "title": f"Trending topic in {subreddit} about {i+1}",
                "subreddit": subreddit,
                "upvotes": 1000 + (i * 100),
                "comments": 100 + (i * 10),
                "url": f"https://www.reddit.com/r/{subreddit}/comments/{i+1}/"
            })
        
        return posts
    except Exception as e:
        logger.error(f"Error fetching from r/{subreddit}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=503, detail=f"Failed to fetch Reddit data: {str(e)}") 