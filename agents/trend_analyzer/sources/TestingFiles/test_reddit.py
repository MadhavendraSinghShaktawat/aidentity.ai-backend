import asyncio
import os
from dotenv import load_dotenv  # You may need to install this: pip install python-dotenv

# Load environment variables from .env file
load_dotenv()

# Check if credentials are loaded
print(f"Client ID present: {'Yes' if os.environ.get('REDDIT_CLIENT_ID') else 'No'}")
print(f"Client Secret present: {'Yes' if os.environ.get('REDDIT_CLIENT_SECRET') else 'No'}")
print(f"User Agent present: {'Yes' if os.environ.get('REDDIT_USER_AGENT') else 'No'}")

from agents.trend_analyzer.sources.reddit import fetch_reddit_trends
from agents.trend_analyzer.schemas import TrendDepth

async def test_fetch_reddit_trends():
    industry = "tech"
    trend_depth = TrendDepth.PAST_WEEK  # Adjust as needed
    keywords = ["AI", "Machine Learning"]  # Example keywords

    try:
        trends = await fetch_reddit_trends(industry, trend_depth, keywords)
        print("Fetched Reddit Trends:")
        print(f"Platform: {trends.platform}")
        print(f"Is Mock Data: {trends.metadata.get('is_mock', False)}")
        print(f"Timestamp: {trends.timestamp}")
        print("\nData:")
        print(trends.raw_data)
    except Exception as e:
        print(f"Error fetching Reddit trends: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_fetch_reddit_trends())