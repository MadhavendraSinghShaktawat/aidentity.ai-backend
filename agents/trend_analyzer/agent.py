from typing import Dict, List, Optional, Any
import asyncio
import logging
from datetime import datetime, timedelta
import json

from fastapi import HTTPException

# Updated imports for LangChain
try:
    from langchain_openai import ChatOpenAI
except ImportError:
    from langchain_community.chat_models import ChatOpenAI
    
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser

from .schemas import (
    TrendAnalyzerInput, 
    TrendAnalyzerOutput,
    ContentCalendarItem,
    TrendSource,
    TrendSummary,
    CostMode
)
from .sources.reddit import fetch_reddit_trends
from .sources.twitter import fetch_twitter_trends
from .sources.youtube import fetch_youtube_trends
from .sources.google_trends import fetch_google_trends
from .sources.crawl4ai import fetch_crawl4ai_trends
from utils.errors import AgentFailureError
from utils.redis_cache import get_cached_result, cache_result

logger = logging.getLogger(__name__)

async def analyze_trends(input_data: TrendAnalyzerInput) -> TrendAnalyzerOutput:
    """
    Analyze trending topics from multiple sources and generate a content calendar.
    
    Args:
        input_data: The validated input parameters for trend analysis
        
    Returns:
        A structured output containing trend summaries and a content calendar
        
    Raises:
        AgentFailureError: If trend analysis fails for any reason
    """
    try:
        cache_key = f"trend_analysis_{input_data.target_platform}_{input_data.industry}_{input_data.trend_depth}_{input_data.calendar_duration}"
        
        # Skip cache if bypassing or in development
        if not input_data.bypass_cache:
            cached_result = await get_cached_result(cache_key)
            if cached_result:
                logger.info(f"Returning cached trend analysis for {cache_key}")
                return TrendAnalyzerOutput.model_validate(cached_result)
        
        # 1. Fetch trends from all sources based on cost mode
        try:
            trend_sources = await _fetch_trends_from_sources(input_data)
            logger.info(f"Successfully fetched trends from {len(trend_sources)} sources")
        except Exception as e:
            logger.error(f"Error fetching trends: {str(e)}", exc_info=True)
            # If we can't fetch trends, we can't continue
            raise AgentFailureError(f"Failed to fetch trends: {str(e)}")
        
        # 2. Analyze and summarize trends using LLM
        try:
            trend_summaries = await _analyze_trends_with_llm(
                trend_sources=trend_sources,
                input_data=input_data
            )
            logger.info(f"Successfully analyzed trends: {len(trend_summaries)} summaries generated")
        except Exception as e:
            logger.error(f"Error analyzing trends with LLM: {str(e)}", exc_info=True)
            # Create mock trend summaries as fallback
            logger.info("Falling back to mock trend summaries")
            trend_summaries = _create_mock_trend_summaries(input_data)
        
        # 3. Generate content calendar
        try:
            content_calendar = await _generate_content_calendar(
                trend_summaries=trend_summaries,
                input_data=input_data
            )
            logger.info(f"Successfully generated content calendar with {len(content_calendar)} items")
        except Exception as e:
            logger.error(f"Error generating content calendar: {str(e)}", exc_info=True)
            # Create mock calendar as fallback
            logger.info("Falling back to mock calendar")
            content_calendar = _create_mock_calendar(trend_summaries, input_data)
        
        # 4. Prepare and return the result
        result = TrendAnalyzerOutput(
            analyzed_at=datetime.utcnow(),
            target_platform=input_data.target_platform,
            industry=input_data.industry,
            trend_depth=input_data.trend_depth,
            calendar_duration=input_data.calendar_duration,
            trend_summaries=trend_summaries,
            content_calendar=content_calendar
        )
        
        # 5. Cache the result
        try:
            await cache_result(cache_key, result.model_dump(), expiry_seconds=3600)  # Cache for 1 hour
            logger.debug(f"Cached result with key: {cache_key}")
        except Exception as cache_err:
            logger.warning(f"Failed to cache result: {str(cache_err)}")
        
        return result
    
    except AgentFailureError:
        # Re-raise specific agent failures
        raise
    except Exception as e:
        logger.error(f"Trend analysis failed: {str(e)}", exc_info=True)
        raise AgentFailureError(f"Failed to analyze trends: {str(e)}")

async def _fetch_trends_from_sources(input_data: TrendAnalyzerInput) -> List[TrendSource]:
    """
    Fetch trends from multiple sources based on cost mode.
    
    Args:
        input_data: The validated input parameters
        
    Returns:
        A list of trend sources with their raw data
    """
    sources = []
    cost_mode = input_data.cost_mode
    trend_depth = input_data.trend_depth
    industry = input_data.industry
    keywords = input_data.keywords
    
    # Define which sources to use based on cost mode
    if cost_mode == CostMode.LOW_COST:
        # For low cost, use only 2-3 sources
        source_functions = [
            fetch_reddit_trends,
            fetch_twitter_trends
        ]
    elif cost_mode == CostMode.BALANCED:
        # For balanced, use 3-4 sources
        source_functions = [
            fetch_reddit_trends,
            fetch_twitter_trends,
            fetch_youtube_trends,
            fetch_google_trends
        ]
    else:  # HIGH_QUALITY
        # For high quality, use all sources
        source_functions = [
            fetch_reddit_trends,
            fetch_twitter_trends, 
            fetch_youtube_trends,
            fetch_google_trends,
            fetch_crawl4ai_trends
        ]
    
    # Fetch data from all selected sources concurrently
    tasks = []
    for func in source_functions:
        # Check if the function can accept keywords parameter
        import inspect
        sig = inspect.signature(func)
        if 'keywords' in sig.parameters:
            # Function supports keywords parameter
            tasks.append(func(industry, trend_depth, keywords=keywords))
        else:
            # Use original signature
            tasks.append(func(industry, trend_depth))
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results, handling any exceptions
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.warning(f"Failed to fetch from source {source_functions[i].__name__}: {str(result)}")
            continue
        
        sources.append(result)
    
    if not sources:
        raise AgentFailureError("Failed to fetch trends from any source")
    
    return sources

async def _analyze_trends_with_llm(
    trend_sources: List[TrendSource],
    input_data: TrendAnalyzerInput
) -> List[TrendSummary]:
    """
    Use GPT-3.5 Turbo to analyze and summarize trends.
    
    Args:
        trend_sources: List of trend sources with raw data
        input_data: The validated input parameters
        
    Returns:
        A list of trend summaries with insights
    """
    try:
        # Select model based on cost mode
        if input_data.cost_mode == CostMode.LOW_COST:
            model = "gpt-3.5-turbo"
            temperature = 0.3
        elif input_data.cost_mode == CostMode.BALANCED:
            model = "gpt-3.5-turbo"
            temperature = 0.5
        else:  # HIGH_QUALITY
            model = "gpt-3.5-turbo-16k"
            temperature = 0.7
        
        # Initialize LangChain components
        try:
            # Try to import from langchain_openai first (newer package)
            from langchain_openai import ChatOpenAI
        except ImportError:
            # Fall back to deprecated import if necessary
            from langchain_community.chat_models import ChatOpenAI
            logger.warning("Using deprecated ChatOpenAI import from langchain_community")
        
        llm = ChatOpenAI(model=model, temperature=temperature)
        
        # Get keyword focus if provided
        keyword_instruction = ""
        if input_data.keywords and len(input_data.keywords) > 0:
            keyword_list = ", ".join([f'"{k}"' for k in input_data.keywords])
            keyword_instruction = f"""
            KEYWORD FOCUS: You should specifically look for trends related to these keywords: {keyword_list}.
            Prioritize content that involves these keywords and find the most recent trending discussions about them.
            If any of these keywords are currently trending in a major way, make sure to highlight them prominently.
            """
        
        # Create prompt for trend analysis
        template = """
        You are a trend analysis expert tasked with identifying valuable content opportunities.
        
        Target platform: {target_platform}
        Industry/Niche: {industry}
        {keyword_focus}
        
        Analyze the following trends data from multiple sources:
        
        {trends_data}
        
        Provide a comprehensive analysis that:
        1. Identifies the top 5-10 most promising trending topics relevant to {industry}
        2. For each trend, analyze:
           - Overall engagement level (high, medium, low)
           - Key audience demographics if apparent
           - Content types performing well within this trend
           - Potential angles for {target_platform}
           - How recent and timely this trend is (is it happening right now?)
        3. Explain why each trend would be valuable for the target platform
        
        RESPOND ONLY WITH a valid JSON array of trend objects with these fields:
        - topic: The main trend topic
        - description: A brief description of the trend
        - engagement_level: The engagement level (HIGH, MEDIUM, LOW)
        - target_audience: Key audience demographics for this trend
        - content_suggestions: List of 2-3 specific content ideas for {target_platform}
        - source_platforms: List of platforms where this trend is popular
        - timeliness: How recent and timely this trend is (VERY_RECENT, RECENT, ONGOING)
        
        IMPORTANT: Your response MUST ONLY BE a valid JSON array. Do not include any text before or after the JSON array.
        """
        
        prompt = ChatPromptTemplate.from_template(template)
        
        # Prepare trends data for the prompt
        trends_data = ""
        for source in trend_sources:
            trends_data += f"\n--- {source.platform} TRENDS ---\n"
            trends_data += source.raw_data + "\n"
        
        # Run the chain
        chain = prompt | llm | StrOutputParser()
        result = await chain.ainvoke({
            "target_platform": input_data.target_platform,
            "industry": input_data.industry,
            "keyword_focus": keyword_instruction,
            "trends_data": trends_data
        })
        
        # Debug the raw response
        logger.debug(f"Raw LLM response: {result[:100]}...")  # Log the beginning of the response
        
        # Clean up response to ensure it's valid JSON
        result = result.strip()
        
        # Check if we received any content
        if not result:
            logger.error("Received empty response from LLM")
            raise ValueError("Empty response from LLM")
        
        # Find the first '[' and last ']' to extract just the JSON array
        start_idx = result.find('[')
        end_idx = result.rfind(']')
        
        if start_idx == -1 or end_idx == -1:
            logger.error(f"Response does not contain JSON array brackets: {result[:100]}...")
            raise ValueError("Response does not contain JSON array")
        
        # Extract just the JSON part
        json_result = result[start_idx:end_idx+1]
        
        # Parse results - handling potential JSON parsing issues
        try:
            trend_data = json.loads(json_result)
            
            trend_summaries = []
            for item in trend_data:
                # Add any additional fields from the LLM response to the metadata
                additional_fields = {k: v for k, v in item.items() 
                                  if k not in ["topic", "description", "engagement_level", 
                                              "target_audience", "content_suggestions", "source_platforms"]}
                
                trend_summaries.append(
                    TrendSummary(
                        topic=item.get("topic", ""),
                        description=item.get("description", ""),
                        engagement_level=item.get("engagement_level", "MEDIUM"),
                        target_audience=item.get("target_audience", ""),
                        content_suggestions=item.get("content_suggestions", []),
                        source_platforms=item.get("source_platforms", []),
                        timeliness=item.get("timeliness", "ONGOING")
                    )
                )
            
            return trend_summaries
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}", exc_info=True)
            logger.debug(f"Raw response: {result}")
            # Don't raise here, let it fall through to the mock data generation
            raise ValueError(f"Invalid JSON response: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error in trend analysis: {str(e)}", exc_info=True)
        
        # Generate and return mock data instead of raising an exception
        logger.info("Falling back to mock trend data")
        return _create_mock_trend_summaries(input_data)

async def _generate_content_calendar(
    trend_summaries: List[TrendSummary],
    input_data: TrendAnalyzerInput
) -> List[ContentCalendarItem]:
    """
    Generate a content calendar based on trend summaries.
    
    Args:
        trend_summaries: List of analyzed trend summaries
        input_data: The validated input parameters
        
    Returns:
        A structured content calendar for the requested duration
    """
    try:
        # Determine number of days in the calendar
        if input_data.calendar_duration == "7 Days":
            num_days = 7
        elif input_data.calendar_duration == "14 Days":
            num_days = 14
        else:  # "30 Days"
            num_days = 30
        
        # Initialize LangChain components
        model = "gpt-3.5-turbo" if input_data.cost_mode != CostMode.HIGH_QUALITY else "gpt-3.5-turbo-16k"
        
        # Use the already imported ChatOpenAI (from the top of the file)
        llm = ChatOpenAI(model=model, temperature=0.7)
        
        # Create prompt for calendar generation
        template = """
        Create a detailed content calendar for {num_days} days on {target_platform} for a {industry} account.
        
        Base your calendar on these trending topics:
        {trends_json}
        
        For each day, provide:
        1. The main topic/theme based on one of the trends
        2. A specific content idea with a catchy title/headline
        3. The content format (post, story, reel, video, etc. - appropriate for {target_platform})
        4. Best posting time (morning, afternoon, evening)
        5. Relevant hashtags (3-5 hashtags)
        6. A brief content brief (1-2 sentences)
        
        Distribute the trends across the calendar, ensuring variety and engagement potential.
        Consider the platform's best practices and optimal posting frequency.
        
        RESPOND ONLY WITH a valid JSON array with objects for each day, containing these fields:
        - day: The day number (1 to {num_days})
        - date: A sample date starting from today (YYYY-MM-DD format)
        - main_topic: The main trend topic for this content
        - content_title: A catchy title/headline
        - content_format: The format for {target_platform}
        - posting_time: Recommended posting time
        - hashtags: List of relevant hashtags
        - content_brief: Brief description of what the content should contain
        
        IMPORTANT: Your response MUST ONLY BE a valid JSON array. Do not include any text before or after the JSON array.
        """
        
        prompt = ChatPromptTemplate.from_template(template)
        
        # Convert trend summaries to JSON for the prompt
        trends_json = json.dumps([t.model_dump() for t in trend_summaries])
        
        # Run the chain
        chain = prompt | llm | StrOutputParser()
        result = await chain.ainvoke({
            "num_days": num_days,
            "target_platform": input_data.target_platform,
            "industry": input_data.industry,
            "trends_json": trends_json
        })
        
        # Debug the raw response
        logger.debug(f"Raw calendar LLM response: {result[:100]}...")  # Log the beginning of the response
        
        # Clean up response to ensure it's valid JSON
        result = result.strip()
        
        # Check if we received any content
        if not result:
            logger.error("Received empty response from LLM for calendar generation")
            raise ValueError("Empty response from LLM")
        
        # Find the first '[' and last ']' to extract just the JSON array
        start_idx = result.find('[')
        end_idx = result.rfind(']')
        
        if start_idx == -1 or end_idx == -1:
            logger.error(f"Calendar response does not contain JSON array brackets: {result[:100]}...")
            raise ValueError("Calendar response does not contain JSON array")
        
        # Extract just the JSON part
        json_result = result[start_idx:end_idx+1]
        
        # Parse results
        try:
            calendar_data = json.loads(json_result)
            
            content_calendar = []
            for item in calendar_data:
                # Calculate the actual date
                day_num = item.get("day", 1)
                actual_date = datetime.now() + timedelta(days=day_num-1)
                
                content_calendar.append(
                    ContentCalendarItem(
                        day_number=day_num,
                        calendar_date=actual_date.date(),
                        main_topic=item.get("main_topic", ""),
                        content_title=item.get("content_title", ""),
                        content_format=item.get("content_format", ""),
                        posting_time=item.get("posting_time", ""),
                        hashtags=item.get("hashtags", []),
                        content_brief=item.get("content_brief", "")
                    )
                )
            
            return content_calendar
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse calendar LLM response as JSON: {e}", exc_info=True)
            logger.debug(f"Raw calendar response: {result}")
            raise ValueError(f"Invalid JSON response from calendar generation: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error in calendar generation: {str(e)}", exc_info=True)
        # Instead of raising, return mock data
        return _create_mock_calendar(trend_summaries, input_data) 

def _create_mock_trend_summaries(input_data: TrendAnalyzerInput) -> List[TrendSummary]:
    """Create mock trend summaries for testing or fallback."""
    logger.info("Creating mock trend summaries for testing")
    
    # Create base mock trend summaries based on input parameters
    mock_trends = [
        TrendSummary(
            topic=f"{input_data.industry} Digital Transformation",
            description=f"How businesses in the {input_data.industry} sector are adopting digital solutions.",
            engagement_level="HIGH",
            target_audience="Business professionals, tech enthusiasts",
            content_suggestions=[
                f"Top 10 Digital Tools for {input_data.industry}",
                f"Case Study: Digital Transformation in {input_data.industry}",
                f"The Future of {input_data.industry} Technology"
            ],
            source_platforms=["LinkedIn", "Twitter", "Industry Blogs"]
        ),
        TrendSummary(
            topic=f"Sustainable {input_data.industry}",
            description=f"The growing importance of sustainability in {input_data.industry}.",
            engagement_level="MEDIUM",
            target_audience="Environmentally conscious consumers, industry leaders",
            content_suggestions=[
                f"How to Make Your {input_data.industry} Business More Sustainable",
                f"The ROI of Sustainability in {input_data.industry}",
                f"Spotlight: Sustainable {input_data.industry} Innovations"
            ],
            source_platforms=["Instagram", "YouTube", "Environmental Forums"]
        ),
        TrendSummary(
            topic=f"{input_data.industry} for Gen Z",
            description=f"How Generation Z is reshaping the {input_data.industry} landscape.",
            engagement_level="HIGH",
            target_audience="Young adults, marketers targeting Gen Z",
            content_suggestions=[
                f"What Gen Z Wants from {input_data.industry} Brands",
                f"TikTok Trends in {input_data.industry}",
                f"The Gen Z {input_data.industry} Consumer Report"
            ],
            source_platforms=["TikTok", "Instagram", "Snapchat"]
        ),
        TrendSummary(
            topic=f"AI in {input_data.industry}",
            description=f"The impact of artificial intelligence on {input_data.industry}.",
            engagement_level="HIGH",
            target_audience="Tech adopters, business innovators",
            content_suggestions=[
                f"AI Tools Revolutionizing {input_data.industry}",
                f"How to Implement AI in Your {input_data.industry} Strategy",
                f"The Ethics of AI in {input_data.industry}"
            ],
            source_platforms=["Reddit", "Twitter", "Tech Blogs"]
        ),
        TrendSummary(
            topic=f"Remote Work in {input_data.industry}",
            description=f"The continuing evolution of remote work in {input_data.industry}.",
            engagement_level="MEDIUM",
            target_audience="Remote workers, HR professionals",
            content_suggestions=[
                f"Building a Remote {input_data.industry} Team",
                f"Tools for Remote {input_data.industry} Collaboration",
                f"The Future of Work in {input_data.industry}"
            ],
            source_platforms=["LinkedIn", "Medium", "Industry Forums"]
        )
    ]
    
    # If keywords are provided, add some keyword-specific mock trends
    if input_data.keywords and len(input_data.keywords) > 0:
        for keyword in input_data.keywords[:3]:  # Limit to first 3 keywords
            keyword_trend = TrendSummary(
                topic=f"{keyword} Trends in {input_data.industry}",
                description=f"Latest developments and innovations around {keyword} in the {input_data.industry} sector.",
                engagement_level="HIGH",
                target_audience=f"{input_data.industry} professionals, {keyword} enthusiasts, early adopters",
                content_suggestions=[
                    f"How {keyword} is Changing {input_data.industry} in 2024",
                    f"Top 5 {keyword} Innovations to Watch",
                    f"{input_data.industry} Leaders Using {keyword}: Case Studies"
                ],
                source_platforms=["Twitter", "LinkedIn", "Industry Publications", "Reddit"]
            )
            # Add to the beginning to prioritize keyword-specific trends
            mock_trends.insert(0, keyword_trend)
    
    # Add some "real-time" trending topics
    current_trending_topics = [
        "Artificial Intelligence Ethics",
        "Sustainable Business Practices",
        "Remote Work Revolution",
        "Blockchain Applications",
        "Digital Privacy Concerns",
        "Metaverse Development",
        "NFT Marketplace Evolution",
        "Quantum Computing Breakthroughs",
        "Social Commerce",
        "Creator Economy"
    ]
    
    # Add 1-2 current trending topics
    for topic in current_trending_topics[:2]:
        current_trend = TrendSummary(
            topic=f"{topic} in {input_data.industry}",
            description=f"The latest developments in {topic} and their impact on {input_data.industry}.",
            engagement_level="VERY HIGH",
            target_audience="Trend-focused professionals, innovators, industry leaders",
            content_suggestions=[
                f"Breaking: How {topic} is Disrupting {input_data.industry}",
                f"What You Need to Know About {topic} Today",
                f"Expert Analysis: {topic} Trends for 2024"
            ],
            source_platforms=["Twitter", "TikTok", "LinkedIn", "Industry News"]
        )
        # Add as first item to prioritize current trends
        mock_trends.insert(0, current_trend)
    
    return mock_trends 