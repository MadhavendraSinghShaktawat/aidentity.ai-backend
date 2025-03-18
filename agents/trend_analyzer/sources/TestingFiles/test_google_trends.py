import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import time

# Add the project root directory to the Python path
# This allows imports to work correctly regardless of where the script is run from
project_root = str(Path(__file__).parents[4])  # Go up 4 levels to reach the project root
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"Added {project_root} to Python path")

# Load environment variables from .env file
env_path = Path(project_root) / '.env'
load_dotenv(dotenv_path=env_path)
print(f"Loaded environment from: {env_path}")

# Now we can import our modules using absolute imports
from agents.trend_analyzer.sources.google_trends import fetch_google_trends
from agents.trend_analyzer.schemas import TrendDepth

async def test_fetch_google_trends():
    """
    Test the fetch_google_trends function with real data.
    """
    # Test parameters
    industry = "AI"
    trend_depth = TrendDepth.PAST_WEEK
    keywords = ["machine learning", "ChatGPT", "neural networks"]

    print(f"Testing Google Trends for industry: {industry}")
    print(f"Trend depth: {trend_depth}")
    print(f"Keywords: {keywords}")
    print("-------------------------------------")

    try:
        # Fetch trends
        trends = await fetch_google_trends(industry, trend_depth, keywords)
        
        # Display results
        print("\nFetched Google Trends:")
        print(f"Platform: {trends.platform}")
        print(f"Is Mock Data: {trends.metadata.get('is_mock', 'Unknown')}")
        print(f"Timestamp: {trends.timestamp}")
        print(f"Keywords Used: {trends.metadata.get('keywords_used', [])}")
        print("\nData:")
        print(trends.raw_data)
        
        # Summary
        if trends.metadata.get('is_mock', True):
            print("\n⚠️ Using mock data (either API call failed or no credentials provided)")
        else:
            print("\n✅ Successfully fetched real Google Trends data!")
            
    except Exception as e:
        print(f"\n❌ Error fetching Google Trends: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Starting Google Trends Test")
    print("==========================")
    
    # Run the test
    asyncio.run(test_fetch_google_trends())
    
    # Test with different parameters
    print("\n\nRunning second test with different parameters")
    print("============================================")
    
    async def run_second_test():
        # Test with different parameters
        industry = "Technology"
        trend_depth = TrendDepth.MONTHLY
        keywords = ["startups", "innovation"]
        
        print(f"Testing Google Trends for industry: {industry}")
        print(f"Trend depth: {trend_depth}")
        print(f"Keywords: {keywords}")
        print("-------------------------------------")
        
        try:
            trends = await fetch_google_trends(industry, trend_depth, keywords)
            print("\nFetched Google Trends:")
            print(f"Platform: {trends.platform}")
            print(f"Is Mock Data: {trends.metadata.get('is_mock', 'Unknown')}")
            print(f"Timestamp: {trends.timestamp}")
            print("\nData Sample (first 300 chars):")
            print(trends.raw_data[:300] + "..." if len(trends.raw_data) > 300 else trends.raw_data)
            
            if not trends.metadata.get('is_mock', True):
                print("\n✅ Successfully fetched real Google Trends data!")
            else:
                print("\n⚠️ Using mock data")
                
        except Exception as e:
            print(f"\n❌ Error fetching Google Trends: {str(e)}")
    
    asyncio.run(run_second_test()) 