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
from agents.trend_analyzer.agent import analyze_trends
from agents.trend_analyzer.schemas import TrendAnalyzerInput, CostMode, TrendDepth, CalendarDuration
from utils.redis_cache import redis_client, close_redis_connection

async def test_agent_with_youtube():
    """
    Test the trend analyzer agent with YouTube data.
    This test specifically configures the agent to use YouTube in the BALANCED mode,
    which will include YouTube but not all possible sources.
    """
    print("\nTesting Trend Analyzer Agent with YouTube Data")
    print("===============================================")
    
    # Create input for the trend analyzer
    input_data = TrendAnalyzerInput(
        industry="Technology",
        target_platform="YouTube",
        trend_depth=TrendDepth.PAST_WEEK,
        calendar_duration=CalendarDuration.WEEK,
        cost_mode=CostMode.BALANCED,  # This will include YouTube
        keywords=["AI", "anime technology"],
        bypass_cache=True  # Force a fresh analysis
    )
    
    print(f"Analyzing trends for {input_data.industry} industry")
    print(f"Keywords: {input_data.keywords}")
    print(f"Cost mode: {input_data.cost_mode}")
    print(f"Trend depth: {input_data.trend_depth}")
    print(f"Target platform: {input_data.target_platform}")
    
    try:
        # Run the trend analyzer
        print("\nRunning trend analysis...")
        result = await analyze_trends(input_data)
        
        # Get the sources that were used in the analysis
        sources = getattr(result, "_sources", []) or []
        youtube_source = None
        
        print("\nSources used in analysis:")
        if not sources:
            print("No source information available (might be using cached result)")
        else:
            for source in sources:
                is_mock = source.metadata.get("is_mock", True)
                print(f"- {source.platform}: {'MOCK' if is_mock else 'REAL'} data")
                
                # Save YouTube source for detailed inspection
                if source.platform == "YouTube":
                    youtube_source = source
        
        if youtube_source:
            is_mock = youtube_source.metadata.get("is_mock", True)
            print(f"\nYouTube Source Found: {'MOCK' if is_mock else 'REAL'} data")
            
            if not is_mock:
                print("\n✅ SUCCESS! Agent is using REAL YouTube data!")
            else:
                print("\n⚠️ Agent is using MOCK YouTube data. Check your API key setup.")
                
            # Display a sample of the YouTube data
            print("\nSample YouTube Data:")
            sample_data = youtube_source.raw_data[:500] + "..." if len(youtube_source.raw_data) > 500 else youtube_source.raw_data
            print(sample_data)
        else:
            print("\n⚠️ No YouTube source found in the results. Check the agent configuration.")
        
        # Show the trend summaries
        print("\nTrend Summaries:")
        for i, summary in enumerate(result.trend_summaries[:3]):  # Show first 3 summaries
            print(f"\n{i+1}. {summary.topic}")
            print(f"   Engagement: {summary.engagement_level}")
            print(f"   Timeliness: {summary.timeliness}")
            print(f"   Sources: {', '.join(summary.source_platforms)}")
            
        # Show first content calendar item
        if result.content_calendar:
            print("\nSample Content Calendar Item:")
            item = result.content_calendar[0]
            print(f"Day {item.day_number}: {item.content_title}")
            print(f"Format: {item.content_format}")
            print(f"Brief: {item.content_brief}")
        
        return result
    
    except Exception as e:
        print(f"\n❌ Error during trend analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("Testing YouTube Integration with Trend Analyzer Agent")
    print("=====================================================")
    
    # Run the test
    result = asyncio.run(test_agent_with_youtube())
    
    print("\nTest completed.") 