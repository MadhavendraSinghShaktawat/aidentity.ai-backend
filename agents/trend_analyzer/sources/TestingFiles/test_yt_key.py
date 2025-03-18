import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import requests

# Add the project root directory to the Python path
project_root = str(Path(__file__).parents[4])  # Go up 4 levels to reach the project root
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"Added {project_root} to Python path")

# Load environment variables from .env file
env_path = Path(project_root) / '.env'
load_dotenv(dotenv_path=env_path)
print(f"Loaded environment from: {env_path}")

# Get YouTube API key
yt_api_key = os.environ.get("YT_GOOGLE_KEY", "")
regular_api_key = os.environ.get("GOOGLE_API_KEY", "")

# Show which keys are available (with partial masking for security)
if yt_api_key:
    masked_key = yt_api_key[:4] + "*" * (len(yt_api_key) - 8) + yt_api_key[-4:]
    print(f"✅ YT_GOOGLE_KEY found: {masked_key}")
else:
    print("❌ YT_GOOGLE_KEY not found in environment variables")

if regular_api_key:
    masked_key = regular_api_key[:4] + "*" * (len(regular_api_key) - 8) + regular_api_key[-4:]
    print(f"✅ GOOGLE_API_KEY found: {masked_key}")
else:
    print("❌ GOOGLE_API_KEY not found in environment variables")

# Test the YouTube API key
api_key = yt_api_key or regular_api_key
if not api_key:
    print("❌ No API key available. Please set YT_GOOGLE_KEY in your .env file")
    sys.exit(1)

print("\nTesting YouTube API connection...")
url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q=test&key={api_key}&maxResults=1"

try:
    response = requests.get(url)
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("\n✅ SUCCESS! YouTube API is working correctly")
        print("\nSample response data:")
        if "items" in data and len(data["items"]) > 0:
            video = data["items"][0]
            print(f"Title: {video['snippet']['title']}")
            print(f"Channel: {video['snippet']['channelTitle']}")
            print(f"Published: {video['snippet']['publishedAt']}")
    else:
        print("\n❌ API returned an error:")
        print(response.text)
        
        if response.status_code == 403 and "accessNotConfigured" in response.text:
            print("\nPossible solutions:")
            print("1. Make sure you've enabled the YouTube Data API v3 for this project")
            print("2. Ensure your API key is from the same project where you enabled the API")
            print("3. Check if your API key has the proper access to YouTube Data API v3")
            print("4. Wait 5-10 minutes after enabling the API for changes to propagate")
        
except Exception as e:
    print(f"\n❌ Error: {str(e)}")

print("\nTest completed.") 