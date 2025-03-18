"""
Test script for the web crawler implementation.

This script tests the web crawler's ability to fetch trending 
topics from web sources for various industries.
"""
import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
import json

# Add the project root directory to the Python path
project_root = str(Path(__file__).parents[4])  # Go up 4 levels to reach the project root
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"Added {project_root} to Python path")

# Load environment variables from .env file
env_path = Path(project_root) / '.env'
load_dotenv(dotenv_path=env_path)
print(f"Loaded environment from: {env_path}")

# Now we can import our modules using absolute imports
from agents.trend_analyzer.sources.crawl4ai import fetch_crawl4ai_trends
from agents.trend_analyzer.schemas import TrendDepth

async def test_web_crawler_for_industry(industry: str, trend_depth: TrendDepth):
    """
    Test the web crawler for a specific industry and trend depth.
    
    Args:
        industry: The industry to analyze
        trend_depth: The trend depth to use
    """
    print(f"\nTesting Web Crawler for {industry} ({trend_depth.value}):")
    print("=" * 50)
    
    # Use some test keywords relevant to each industry
    keywords = []
    if industry == "Technology":
        keywords = ["AI", "machine learning", "blockchain"]
    elif industry == "Marketing":
        keywords = ["social media", "digital marketing", "SEO"]
    elif industry == "Finance":
        keywords = ["cryptocurrency", "investing", "fintech"]
    elif industry == "Health":
        keywords = ["wellness", "mental health", "fitness"]
    
    try:
        # Fetch trends using the crawler
        result = await fetch_crawl4ai_trends(
            industry=industry,
            trend_depth=trend_depth,
            keywords=keywords
        )
        
        # Check if we got real or mock data
        is_mock = result.metadata.get("is_mock", True)
        
        if is_mock:
            print(f"⚠️ Using MOCK data for {industry}")
        else:
            print(f"✅ Using REAL crawled data for {industry}")
        
        # Print metadata
        print("\nMetadata:")
        for key, value in result.metadata.items():
            print(f"- {key}: {value}")
        
        # Print raw data (limited to first 700 chars)
        print("\nSample Data:")
        sample_data = result.raw_data[:700] + "..." if len(result.raw_data) > 700 else result.raw_data
        print(sample_data)
        
        return result
        
    except Exception as e:
        print(f"❌ Error testing Web Crawler for {industry}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    """Run tests for multiple industries and trend depths."""
    print("Testing Web Crawler Integration")
    print("==============================")
    
    # Test a variety of industries
    industries = ["Technology", "Marketing", "Health"]
    
    # Test different trend depths
    await test_web_crawler_for_industry("Technology", TrendDepth.PAST_WEEK)
    await test_web_crawler_for_industry("Marketing", TrendDepth.LAST_24H)
    await test_web_crawler_for_industry("Health", TrendDepth.MONTHLY)
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    asyncio.run(main()) 