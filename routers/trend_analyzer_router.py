"""
Trend Analyzer Router

This module defines the API endpoints for the Trend Analyzer agent,
which analyzes trending topics and generates content calendars.
"""
import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, Request
from fastapi.responses import HTMLResponse

from agents.trend_analyzer.agent import analyze_trends
from agents.trend_analyzer.schemas import (
    TrendAnalyzerInput,
    TrendAnalyzerOutput,
    CostMode,
    TrendDepth,
    CalendarDuration,
    SupportedPlatformsResponse
)
from agents.trend_analyzer.sources.google_trends import get_oauth_authorization_url
from utils.errors import AgentFailureError

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

@router.post("/analyze", response_model=TrendAnalyzerOutput)
async def trend_analysis(
    input_data: TrendAnalyzerInput
) -> TrendAnalyzerOutput:
    """
    Analyze trending topics and generate a content calendar.
    
    This endpoint fetches trends from multiple sources based on the specified parameters,
    analyzes them, and generates a content calendar tailored to the target platform.
    
    You can now use the optional 'keywords' parameter to focus on specific niche topics.
    For example, if your industry is "Tech", you can add keywords like ["AI", "machine learning", 
    "quantum computing"] to specifically analyze trends related to those topics.
    
    Args:
        input_data: Input parameters for trend analysis, including:
            - target_platform: Platform to create content for (e.g., Instagram)
            - industry: Industry or niche (e.g., Tech, Fitness)
            - trend_depth: How far back to analyze (Past Week, Monthly)
            - calendar_duration: Duration of content calendar (7 Days, 14 Days, 30 Days)
            - cost_mode: Balance of cost/quality (Low-Cost, Balanced, High-Quality)
            - bypass_cache: Whether to skip cached results (default: False)
            - keywords: Optional list of specific topics to focus on (e.g., ["AI", "Web3", "startups"])
        
    Returns:
        A structured output containing trend summaries and a content calendar
    """
    try:
        logger.info(f"Receiving trend analysis request for {input_data.target_platform} in {input_data.industry}")
        if input_data.keywords:
            logger.info(f"With keyword focus: {', '.join(input_data.keywords)}")
        
        result = await analyze_trends(input_data)
        return result
    except AgentFailureError as e:
        logger.error(f"Trend analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during trend analysis: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred during trend analysis")

@router.post("/analyze-async", status_code=202)
async def analyze_trends_async(
    input_data: TrendAnalyzerInput,
    background_tasks: BackgroundTasks
):
    """
    Start an asynchronous trend analysis job.
    
    This endpoint queues a trend analysis job to run in the background and returns immediately.
    The client should poll the job status endpoint to check for completion.
    """
    try:
        logger.info(f"Starting async trend analysis for {input_data.target_platform} in {input_data.industry}")
        # Add the task to background tasks
        # In a real implementation, you'd store the task ID and results
        background_tasks.add_task(analyze_trends, input_data)
        
        return {
            "status": "accepted",
            "message": "Trend analysis job has been queued",
            "job_id": "not-implemented-yet"  # In a real implementation, generate a UUID
        }
    except Exception as e:
        logger.error(f"Failed to start async trend analysis: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to start trend analysis")

@router.get("/supported-platforms", response_model=SupportedPlatformsResponse)
async def get_supported_platforms():
    """
    Get a list of supported platforms and other options for trend analysis.
    """
    return SupportedPlatformsResponse(
        platforms=["Instagram", "TikTok", "LinkedIn", "Twitter", "Facebook", "YouTube"],
        trend_depths=["Past Week", "Past Month", "Past 3 Months"],
        calendar_durations=["7 Days", "14 Days", "30 Days"],
        cost_modes=["Low Cost", "Balanced", "High Quality"]
    )

@router.get("/google-auth", response_class=HTMLResponse)
async def start_google_auth():
    """
    Start the Google OAuth flow for Trends API access.
    
    This endpoint generates a Google OAuth URL and redirects the user to it.
    After authentication, Google will redirect back to the specified redirect URI.
    """
    try:
        auth_url = get_oauth_authorization_url()
        
        # Return an HTML page that redirects to the Google auth URL
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Redirecting to Google Auth</title>
            <meta http-equiv="refresh" content="0;url={auth_url}">
        </head>
        <body>
            <h1>Redirecting to Google Authentication...</h1>
            <p>If you are not redirected automatically, <a href="{auth_url}">click here</a>.</p>
        </body>
        </html>
        """
    except ValueError as e:
        # Handle the case where credentials are missing
        error_message = str(e)
        logger.error(f"OAuth error: {error_message}")
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authentication Error</title>
        </head>
        <body>
            <h1>Google Authentication Setup Error</h1>
            <p>The application is not correctly configured for Google authentication.</p>
            <p>Error details: {error_message}</p>
            <h2>How to Fix This Issue:</h2>
            <ol>
                <li>Make sure you've created OAuth credentials in the Google Cloud Console</li>
                <li>Add your Google Client ID to the .env file as GOOGLE_CLIENT_ID</li>
                <li>Verify that your application is loading environment variables correctly</li>
                <li>Check the server logs for more detailed information</li>
            </ol>
        </body>
        </html>
        """

@router.get("/redirect", response_class=HTMLResponse)
async def google_auth_redirect(request: Request):
    """
    Handle the redirect from Google OAuth.
    
    This endpoint processes the OAuth response from Google,
    extracts the access token, and stores it for API requests.
    """
    # In a production app, you would extract and store the token
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Authentication Complete</title>
        <script>
            // Extract access token from URL fragment
            const params = new URLSearchParams(window.location.hash.substring(1));
            const accessToken = params.get('access_token');
            
            if (accessToken) {
                // Display success message
                document.addEventListener('DOMContentLoaded', () => {
                    document.getElementById('token').textContent = accessToken;
                    // In a real app, you would send this token to your backend
                });
            }
        </script>
    </head>
    <body>
        <h1>Google Authentication Complete</h1>
        <p>Your access token: <code id="token">Processing...</code></p>
        <p>You can now close this window and return to the application.</p>
    </body>
    </html>
    """ 