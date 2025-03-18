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

# Check if YouTube API key is available
youtube_api_key = os.environ.get("GOOGLE_API_KEY")
if not youtube_api_key:
    print("⚠️ WARNING: GOOGLE_API_KEY not found in environment variables.")
    print("The test will fall back to mock data.")
else:
    print(f"✅ GOOGLE_API_KEY found in environment variables.")

# Now we can import our modules using absolute imports
from agents.trend_analyzer.sources.youtube import fetch_youtube_trends
from agents.trend_analyzer.schemas import TrendDepth

# Print the available TrendDepth values for debugging
print("Available TrendDepth values:", [e.name for e in TrendDepth])

async def test_fetch_youtube_trends(industry, trend_depth, keywords=None):
    """
    Test the fetch_youtube_trends function with specified parameters.
    
    Args:
        industry: The industry to analyze
        trend_depth: How far back to analyze trends
        keywords: Optional list of specific keywords to focus on
    """
    print(f"\n{'='*50}")
    print(f"Testing YouTube Trends for: {industry}")
    print(f"Trend depth: {trend_depth}")
    if keywords:
        print(f"Keywords: {keywords}")
    print(f"{'='*50}")
    
    start_time = time.time()
    
    try:
        # Call the function with the specified parameters
        trends = await fetch_youtube_trends(industry, trend_depth, keywords)
        
        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        
        # Display the results
        print("\nRESULTS:")
        print(f"Platform: {trends.platform}")
        print(f"Is Mock Data: {trends.metadata.get('is_mock', False)}")
        print(f"Analysis Time: {elapsed_time:.2f} seconds")
        print(f"Timestamp: {trends.timestamp}")
        print(f"Keywords Used: {trends.metadata.get('keywords_used', [])}")
        
        # Show a sample of the raw data (first 800 characters)
        print("\nSAMPLE DATA:")
        sample_data = trends.raw_data[:800] + "..." if len(trends.raw_data) > 800 else trends.raw_data
        print(sample_data)
        
        # Check if we got mock data or real data
        if trends.metadata.get('is_mock', False):
            print("\n⚠️ Using mock data (either API key missing or API call failed)")
        else:
            print("\n✅ Successfully fetched real YouTube trends data!")
        
        # Optional: Save the full data to a file for detailed inspection
        save_to_file = False  # Set to True if you want to save the full output
        if save_to_file:
            output_file = Path(__file__).parent / f"youtube_trends_{industry.replace(' ', '_')}.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(trends.raw_data)
            print(f"\nFull data saved to: {output_file}")
            
        return trends
        
    except Exception as e:
        # Handle any exceptions
        print(f"\n❌ Error fetching YouTube trends: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

async def run_tests():
    """Run multiple tests with different parameters."""
    
    # Use the first available TrendDepth value for a short timeframe (should be PAST_WEEK or similar)
    short_timeframe = TrendDepth.PAST_WEEK  # This should exist based on your schema
    
    # Use a longer timeframe (should be MONTHLY or similar)
    long_timeframe = TrendDepth.MONTHLY  # This should exist based on your schema
    
    # Test 1: Tech industry, short timeframe
    await test_fetch_youtube_trends("Technology", short_timeframe, ["AI", "innovation"])
    
    # Wait a bit to avoid rate limiting
    time.sleep(2)
    
    # Test 2: Business industry, long timeframe
    await test_fetch_youtube_trends("Business", long_timeframe, ["entrepreneurship", "startup"])
    
    # Wait a bit to avoid rate limiting
    time.sleep(2)
    
    # Test 3: Specific niche, short timeframe, no keywords
    await test_fetch_youtube_trends("Data Science", short_timeframe)

if __name__ == "__main__":
    print("YouTube Trends Analyzer Test")
    print("===========================")
    
    asyncio.run(run_tests())
    
    print("\nAll tests completed.") 