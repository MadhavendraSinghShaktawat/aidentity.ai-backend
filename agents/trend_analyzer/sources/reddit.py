"""
Reddit Trends Source

This module fetches trending topics from Reddit using the official Reddit API via PRAW.
"""
import logging
import asyncio
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import re

import praw
from praw.models import Submission, Subreddit
from prawcore.exceptions import PrawcoreException
from fastapi import HTTPException

from ..schemas import TrendSource, TrendDepth

logger = logging.getLogger(__name__)

# Reddit API credentials from environment variables
REDDIT_CLIENT_ID = os.environ.get("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.environ.get("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.environ.get("REDDIT_USER_AGENT", "aidentity-trend-analyzer/1.0")

def _initialize_reddit_client() -> Optional[praw.Reddit]:
    """
    Initialize Reddit API client using credentials from environment variables.
    
    Returns:
        Initialized Reddit client or None if credentials are missing
    """
    if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
        logger.warning("Reddit API credentials not found in environment variables")
        return None
    
    try:
        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT
        )
        logger.debug("Successfully initialized Reddit client")
        return reddit
    except Exception as e:
        logger.error(f"Failed to initialize Reddit client: {str(e)}", exc_info=True)
        return None

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
    # Set time filter based on trend depth
    time_filter = "day"
    if trend_depth == "Past Week":
        time_filter = "week"
    elif trend_depth == "Monthly":
        time_filter = "month"
    
    # Get relevant subreddits
    subreddits = await _get_relevant_subreddits(industry, keywords)
    
    # Try to initialize Reddit client
    reddit = _initialize_reddit_client()
    
    if reddit:
        try:
            # Fetch real Reddit data
            logger.info(f"Fetching actual Reddit data for {industry} with depth {trend_depth}")
            raw_data = await _fetch_reddit_data(reddit, subreddits, time_filter, keywords, industry)
            is_mock = False
        except Exception as e:
            logger.error(f"Error fetching Reddit data: {str(e)}", exc_info=True)
            logger.info("Falling back to mock data due to API error")
            raw_data = _generate_mock_reddit_data(industry, subreddits, time_filter, keywords)
            is_mock = True
    else:
        # Fallback to mock data if Reddit client initialization fails
        logger.info(f"Using mock Reddit data (no API credentials) for {industry} with depth {trend_depth}")
        raw_data = _generate_mock_reddit_data(industry, subreddits, time_filter, keywords)
        is_mock = True
    
    # Create and return the trend source object
    return TrendSource(
        platform="Reddit",
        raw_data=raw_data,
        timestamp=datetime.utcnow(),
        metadata={
            "subreddits": subreddits,
            "time_range": str(trend_depth),
            "is_mock": is_mock,
            "keywords_used": keywords
        }
    )

async def _fetch_reddit_data(
    reddit: praw.Reddit,
    subreddits: List[str],
    time_filter: str,
    keywords: Optional[List[str]] = None,
    industry: str = ""
) -> str:
    """
    Fetch actual Reddit data using PRAW.
    
    Args:
        reddit: Initialized PRAW Reddit client
        subreddits: List of subreddit names to fetch from
        time_filter: Time filter for posts
        keywords: Optional list of specific keywords to focus on
        industry: The industry context for additional filtering
        
    Returns:
        Formatted string containing Reddit data
    """
    # Run Reddit API calls in a thread pool since PRAW is synchronous
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None, lambda: _fetch_reddit_data_sync(reddit, subreddits, time_filter, keywords, industry)
    )
    return result

def _fetch_reddit_data_sync(
    reddit: praw.Reddit, 
    subreddits: List[str],
    time_filter: str,
    keywords: Optional[List[str]] = None,
    industry: str = ""
) -> str:
    """
    Synchronous function to fetch Reddit data (to be run in executor).
    
    Args:
        reddit: Initialized PRAW Reddit client
        subreddits: List of subreddit names to fetch from
        time_filter: Time filter for posts
        keywords: Optional list of specific keywords to focus on
        industry: The industry context for additional filtering
        
    Returns:
        Formatted string containing Reddit data
    """
    result = f"Reddit trending topics for {industry}"
    if keywords:
        result += f" with focus on: {', '.join(keywords)}"
    result += f":\n\n"
    
    keyword_regex = None
    if keywords:
        # Create regex pattern to match any of the keywords
        pattern = "|".join(re.escape(keyword) for keyword in keywords)
        keyword_regex = re.compile(pattern, re.IGNORECASE)
    
    # Keep track of all fetched posts for sentiment and keyword analysis
    all_posts = []
    all_post_titles = []
    
    # Limit to top 3-5 most relevant subreddits to avoid excessive API calls
    for subreddit_name in subreddits[:5]:
        try:
            subreddit = reddit.subreddit(subreddit_name)
            
            # Verify the subreddit exists and is accessible
            _ = subreddit.display_name
            
            result += f"r/{subreddit_name} - Top trending discussions ({time_filter}):\n"
            
            # Fetch top posts
            posts = []
            for post in subreddit.top(time_filter=time_filter, limit=25):
                # Skip pinned posts as they're not typically trending content
                if post.stickied:
                    continue
                
                # If keywords are provided, check for relevance
                post_relevance = "medium"
                if keyword_regex and (keyword_regex.search(post.title) or 
                                    (post.selftext and keyword_regex.search(post.selftext))):
                    post_relevance = "high"
                
                # Only include high relevance posts if keywords are provided
                if keywords and post_relevance != "high" and len(posts) >= 10:
                    continue
                
                posts.append({
                    "title": post.title,
                    "upvotes": post.score,
                    "comments": post.num_comments,
                    "url": f"https://www.reddit.com{post.permalink}",
                    "relevance": post_relevance,
                    "created_utc": post.created_utc,
                    "text": post.selftext[:300] + "..." if post.selftext and len(post.selftext) > 300 else post.selftext
                })
                
                all_posts.append(post)
                all_post_titles.append(post.title)
                
                # Limit to top 25 posts per subreddit
                if len(posts) >= 25:
                    break
            
            # Sort by upvotes
            posts.sort(key=lambda x: x["upvotes"], reverse=True)
            
            # Add posts to the result
            for i, post in enumerate(posts[:5]):  # Limit to top 5 posts
                relevance_tag = "[HIGHLY RELEVANT] " if post["relevance"] == "high" else ""
                result += f"{i+1}. {relevance_tag}\"{post['title']}\" - {post['upvotes']} upvotes, {post['comments']} comments\n"
            
            # Extract common keywords from titles and text
            common_keywords = _extract_common_keywords(posts, industry, keywords)
            result += f"\nCommon keywords in r/{subreddit_name}: {', '.join(common_keywords)}\n\n"
            
        except PrawcoreException as e:
            # Handle Reddit API specific errors
            logger.warning(f"Error accessing r/{subreddit_name}: {str(e)}")
            result += f"Error accessing r/{subreddit_name}: {str(e)}\n\n"
        except Exception as e:
            logger.warning(f"General error with r/{subreddit_name}: {str(e)}")
            result += f"Could not fetch data from r/{subreddit_name}\n\n"
    
    # Add overall analysis and metadata
    if all_posts:
        # Get overall statistics
        total_posts = len(all_posts)
        total_engagement = sum(post.score + post.num_comments for post in all_posts)
        result += f"Total posts analyzed: {total_posts}\n"
        result += f"Total engagement: {total_engagement}\n"
        
        # Keyword analysis if keywords were provided
        if keywords and keyword_regex:
            result += f"\nKEYWORD ANALYSIS:\n"
            for keyword in keywords:
                # Count posts matching this keyword
                matches = sum(1 for title in all_post_titles if re.search(re.escape(keyword), title, re.IGNORECASE))
                if matches > 0:
                    percentage = (matches / len(all_post_titles)) * 100
                    result += f"- \"{keyword}\": Found in {matches} posts ({percentage:.1f}% of analyzed content)\n"
                else:
                    result += f"- \"{keyword}\": Not found in analyzed posts\n"
    
    return result

def _extract_common_keywords(
    posts: List[Dict[str, Any]], 
    industry: str, 
    user_keywords: Optional[List[str]] = None
) -> List[str]:
    """
    Extract common keywords from post titles and text.
    
    Args:
        posts: List of post dictionaries
        industry: The industry context
        user_keywords: Optional list of user-provided keywords
        
    Returns:
        List of common keywords
    """
    # Common stop words to filter out
    stop_words = {
        "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", 
        "are", "as", "at", "be", "because", "been", "before", "being", "below", "between", 
        "both", "but", "by", "can", "did", "do", "does", "doing", "down", "during", "each", 
        "few", "for", "from", "further", "had", "has", "have", "having", "he", "he'd", "he'll", 
        "he's", "her", "here", "here's", "hers", "herself", "him", "himself", "his", "how", 
        "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "it", "it's", 
        "its", "itself", "let's", "me", "more", "most", "my", "myself", "nor", "of", "on", 
        "once", "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over", 
        "own", "same", "she", "she'd", "she'll", "she's", "should", "so", "some", "such", 
        "than", "that", "that's", "the", "their", "theirs", "them", "themselves", "then", 
        "there", "there's", "these", "they", "they'd", "they'll", "they're", "they've", 
        "this", "those", "through", "to", "too", "under", "until", "up", "very", "was", 
        "we", "we'd", "we'll", "we're", "we've", "were", "what", "what's", "when", "when's", 
        "where", "where's", "which", "while", "who", "who's", "whom", "why", "why's", "with", 
        "would", "you", "you'd", "you'll", "you're", "you've", "your", "yours", "yourself", 
        "yourselves"
    }
    
    # Common keywords in almost any post
    common_fillers = {"just", "like", "get", "one", "really", "new", "time", "good", "need", 
                     "people", "know", "anyone", "help", "make", "way", "day", "anyone", "else"}
    
    # Combine stop words and common fillers
    filtered_words = stop_words.union(common_fillers)
    
    # Extract all words from titles
    all_words = []
    for post in posts:
        # Split title into words
        title_words = re.findall(r'\b\w+\b', post["title"].lower())
        all_words.extend([word for word in title_words if word not in filtered_words and len(word) > 2])
        
        # Add words from post text if available
        if "text" in post and post["text"]:
            text_words = re.findall(r'\b\w+\b', post["text"].lower())
            all_words.extend([word for word in text_words if word not in filtered_words and len(word) > 2])
    
    # Count word frequencies
    word_counts = {}
    for word in all_words:
        word_counts[word] = word_counts.get(word, 0) + 1
    
    # Sort by frequency
    sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
    
    # Get top keywords, ensuring we include user keywords if they're actually present
    top_keywords = [word for word, count in sorted_words[:15] if count > 1]
    
    # Add industry as a keyword if not already in list
    industry_keywords = industry.lower().split()
    for keyword in industry_keywords:
        if keyword not in filtered_words and keyword not in top_keywords and len(keyword) > 2:
            top_keywords.append(keyword)
    
    # Ensure user keywords are included if they're in the data
    if user_keywords:
        for keyword in user_keywords:
            keyword_lower = keyword.lower()
            # Add keyword if it's in the word counts and not already in top_keywords
            if keyword_lower in word_counts and keyword_lower not in top_keywords:
                top_keywords.append(keyword_lower)
    
    # Limit to 10 keywords
    return top_keywords[:10]

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

# Keep the mock data generation function as a fallback
def _generate_mock_reddit_data(
    industry: str, 
    subreddits: List[str], 
    time_filter: str, 
    keywords: Optional[List[str]] = None
) -> str:
    """
    Generate mock Reddit data for fallback when API is unavailable.
    
    Args:
        industry: The industry or niche
        subreddits: List of relevant subreddits
        time_filter: Time filter (day, week, month)
        keywords: Optional list of specific keywords to focus on
        
    Returns:
        String containing mock Reddit data
    """
    result = f"Reddit trending topics for {industry} (MOCK DATA - API UNAVAILABLE)"
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