"""
Authentication router for AIdentity.ai backend.

This module provides routes for user authentication.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import os
import urllib.parse

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.security import OAuth2AuthorizationCodeBearer
from pydantic import BaseModel, EmailStr

from services.auth_service import AuthService
from utils.auth import Token, create_access_token, get_current_user, get_optional_user
from utils.config import Config
from utils.db import get_collection
from utils.errors import AuthenticationError

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)

# Define OAuth2 scheme for Google login
oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl="https://accounts.google.com/o/oauth2/auth",
    tokenUrl="https://oauth2.googleapis.com/token",
)

# Test login request model
class TestLoginRequest(BaseModel):
    email: EmailStr
    name: str = "Test User"

# Get OAuth configuration from environment variables
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:8001/api/auth/callback/google")

# For frontend integration
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")

def get_google_oauth_url() -> str:
    """
    Generate Google OAuth URL with proper parameters.
    
    Returns:
        Properly formatted Google OAuth URL
    """
    # Validate required environment variables
    if not GOOGLE_CLIENT_ID:
        logger.error("GOOGLE_CLIENT_ID environment variable is missing")
        raise ValueError("Google Client ID is not configured")
        
    if not GOOGLE_REDIRECT_URI:
        logger.error("GOOGLE_REDIRECT_URI environment variable is missing")
        raise ValueError("Google Redirect URI is not configured")
    
    # Base URL for Google OAuth
    base_url = "https://accounts.google.com/o/oauth2/auth"
    
    # Required OAuth parameters
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "email profile",
        "access_type": "offline",
        "prompt": "consent"
    }
    
    # Log the parameters for debugging
    logger.debug(f"Google OAuth parameters: {params}")
    
    # Build and encode the URL
    query_string = urllib.parse.urlencode(params)
    auth_url = f"{base_url}?{query_string}"
    
    # Log the full URL for debugging
    logger.debug(f"Generated Google OAuth URL: {auth_url}")
    
    return auth_url

@router.post("/test-login")
async def test_login(request: TestLoginRequest):
    """
    Test login endpoint that doesn't require Google OAuth.
    This is for development and testing purposes only.
    
    Args:
        request: Login request with email and name
        
    Returns:
        Token: Authentication token
    """
    if not Config.DEV_MODE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Test login is only available in development mode"
        )
    
    try:
        # Check if user exists
        users_collection = get_collection("users")
        user = await users_collection.find_one({"email": request.email})
        
        # Create user if not exists
        if not user:
            # Generate username from email
            username = request.email.split("@")[0]
            
            # Check if username exists
            existing_user = await users_collection.find_one({"username": username})
            if existing_user:
                # Append random suffix to username
                import secrets
                username = f"{username}_{secrets.token_hex(4)}"
            
            # Create new user
            now = datetime.utcnow()
            user = {
                "_id": str(ObjectId()),
                "email": request.email,
                "username": username,
                "full_name": request.name,
                "role": "user",
                "preferences": {
                    "theme": "light",
                    "notifications_enabled": True,
                    "content_preferences": {}
                },
                "auth_provider": "test",
                "auth_provider_id": "test",
                "is_active": True,
                "is_verified": True,
                "profile_picture": None,
                "created_at": now,
                "updated_at": now
            }
            
            # Insert user into database
            await users_collection.insert_one(user)
            logger.info(f"Created new test user: {request.email}")
        
        # Create access token
        expires_delta = timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = await create_access_token(
            data={"sub": user["_id"], "email": request.email},
            expires_delta=expires_delta
        )
        
        # Return token
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=Config.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=user["_id"],
            email=request.email,
            username=user["username"],
            full_name=user.get("full_name")
        )
    except Exception as e:
        logger.exception(f"Test login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create test login: {str(e)}"
        )

@router.get("/login/google")
async def login_google(debug: bool = False):
    """
    Initiate Google OAuth flow.
    
    Args:
        debug: If True, display debug information instead of redirecting
        
    Returns:
        Redirect to Google authentication
    """
    try:
        # Generate the OAuth URL
        auth_url = get_google_oauth_url()
        logger.info("Redirecting to Google authentication")
        
        # Debug information
        client_id_preview = GOOGLE_CLIENT_ID[:5] + "..." if GOOGLE_CLIENT_ID and len(GOOGLE_CLIENT_ID) > 5 else "NOT SET"
        logger.debug(f"Using client_id: {client_id_preview}")
        logger.debug(f"Using redirect_uri: {GOOGLE_REDIRECT_URI}")
        
        # If debug mode, return debug info instead of redirecting
        if debug:
            return HTMLResponse(f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Google OAuth Debug</title>
                <style>
                    body {{ font-family: Arial, sans-serif; padding: 20px; max-width: 800px; margin: 0 auto; }}
                    h1 {{ color: #333; }}
                    .url {{ word-break: break-all; background-color: #f5f5f5; padding: 10px; border-radius: 4px; margin: 10px 0; }}
                    .params {{ margin-bottom: 20px; }}
                    .param {{ margin: 5px 0; }}
                    .button {{ display: inline-block; padding: 10px 15px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 4px; }}
                </style>
            </head>
            <body>
                <h1>Google OAuth Debug Info</h1>
                
                <h2>Generated OAuth URL:</h2>
                <div class="url">{auth_url}</div>
                
                <h2>URL Parameters:</h2>
                <div class="params">
                    <div class="param"><strong>client_id:</strong> {client_id_preview}</div>
                    <div class="param"><strong>redirect_uri:</strong> {GOOGLE_REDIRECT_URI}</div>
                    <div class="param"><strong>response_type:</strong> code</div>
                    <div class="param"><strong>scope:</strong> email profile</div>
                </div>
                
                <p>Click the button below to continue with the OAuth flow:</p>
                <a href="{auth_url}" class="button">Continue to Google Login</a>
                
                <p><a href="/api/auth/diagnostic">⬅️ Back to Diagnostic</a></p>
            </body>
            </html>
            """)
        
        # Use status_code=302 to force a redirect instead of 200
        return RedirectResponse(url=auth_url, status_code=302)
    except ValueError as e:
        # Log the error and provide a helpful message
        logger.error(f"Failed to generate Google OAuth URL: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Authentication configuration error: {str(e)}")

@router.get("/callback/google")
async def google_auth_callback(code: Optional[str] = None, error: Optional[str] = None):
    """
    Handle callback from Google OAuth.
    
    Args:
        code: Authorization code from Google
        error: Error message if authentication failed
        
    Returns:
        Redirect to frontend with auth result
    """
    if error:
        logger.error(f"Google authentication error: {error}")
        return RedirectResponse(url=f"{FRONTEND_URL}/auth/error?error={urllib.parse.quote(error)}")
    
    if not code:
        logger.error("No authorization code received from Google")
        return RedirectResponse(url=f"{FRONTEND_URL}/auth/error?error=no_code")
    
    try:
        # In a real implementation, you would:
        # 1. Exchange the code for an access token
        # 2. Get user info from Google
        # 3. Create or update the user in your database
        # 4. Generate a session or JWT token
        
        # For now, we'll just log the success and redirect to the frontend
        logger.info("Successfully received authorization code from Google")
        
        # Redirect to frontend with success
        return RedirectResponse(url=f"{FRONTEND_URL}/auth/success?provider=google")
    except Exception as e:
        logger.error(f"Error processing Google callback: {str(e)}", exc_info=True)
        return RedirectResponse(url=f"{FRONTEND_URL}/auth/error?error={urllib.parse.quote(str(e))}")

@router.get("/logout")
async def logout():
    """
    Log out the current user.
    
    Returns:
        Success message
    """
    # In a real implementation, you would invalidate the user's token or session
    
    return {
        "message": "Successfully logged out"
    }

@router.get("/me")
async def get_current_user():
    """
    Get the current authenticated user.
    
    Returns:
        User information
    """
    # In a real implementation, you would verify the user's token
    # and return their profile information
    
    return {
        "id": "mock-user-id",
        "email": "user@example.com",
        "name": "Test User",
        "is_authenticated": True
    }

@router.get("/diagnostic", response_class=HTMLResponse)
async def auth_diagnostic():
    """
    Diagnostic page to troubleshoot authentication configuration.
    
    Returns:
        HTML page with diagnostic information
    """
    # Check environment variables
    client_id = GOOGLE_CLIENT_ID
    client_secret = GOOGLE_CLIENT_SECRET
    redirect_uri = GOOGLE_REDIRECT_URI
    
    # Create diagnostic information
    client_id_status = "✅ Set" if client_id else "❌ Missing"
    client_secret_status = "✅ Set" if client_secret else "❌ Missing"
    redirect_uri_status = "✅ Set" if redirect_uri else "❌ Missing"
    
    # Mask sensitive information
    masked_client_id = f"{client_id[:5]}..." if client_id and len(client_id) > 5 else "Not set"
    masked_client_secret = f"{client_secret[:3]}..." if client_secret and len(client_secret) > 3 else "Not set"
    
    # Create HTML content
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>OAuth Diagnostic</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; padding: 20px; max-width: 800px; margin: 0 auto; }}
            h1 {{ color: #333; }}
            .status {{ margin-bottom: 20px; padding: 15px; border-radius: 5px; }}
            .error {{ background-color: #ffeeee; border: 1px solid #ffcccc; }}
            .success {{ background-color: #eeffee; border: 1px solid #ccffcc; }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
            th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background-color: #f2f2f2; }}
            .code {{ font-family: monospace; background-color: #f5f5f5; padding: 3px; }}
            .button {{ display: inline-block; padding: 10px 15px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 4px; }}
        </style>
    </head>
    <body>
        <h1>OAuth Configuration Diagnostic</h1>
        
        <div class="status {'error' if not (client_id and client_secret and redirect_uri) else 'success'}">
            <h2>Configuration Status</h2>
            <p>{'❌ Your OAuth configuration is incomplete. See details below.' if not (client_id and client_secret and redirect_uri) else '✅ Your OAuth configuration appears to be complete.'}</p>
        </div>
        
        <h2>Environment Variables</h2>
        <table>
            <tr>
                <th>Variable</th>
                <th>Status</th>
                <th>Value</th>
            </tr>
            <tr>
                <td>GOOGLE_CLIENT_ID</td>
                <td>{client_id_status}</td>
                <td>{masked_client_id}</td>
            </tr>
            <tr>
                <td>GOOGLE_CLIENT_SECRET</td>
                <td>{client_secret_status}</td>
                <td>{masked_client_secret}</td>
            </tr>
            <tr>
                <td>GOOGLE_REDIRECT_URI</td>
                <td>{redirect_uri_status}</td>
                <td>{redirect_uri or "Not set"}</td>
            </tr>
        </table>
        
        <h2>Test OAuth Flow</h2>
        <p>
            <a href="/api/auth/login/google" class="button">Test Google Login</a>
        </p>
        
        <h2>Manual Configuration</h2>
        <p>If you need to configure OAuth manually, here's how:</p>
        <ol>
            <li>Go to <a href="https://console.cloud.google.com/apis/credentials" target="_blank">Google Cloud Console</a></li>
            <li>Create or select a project</li>
            <li>Go to "Credentials" and click "Create Credentials" > "OAuth client ID"</li>
            <li>Set application type to "Web application"</li>
            <li>Add "{redirect_uri or 'YOUR_BACKEND_URL/api/auth/callback/google'}" to authorized redirect URIs</li>
            <li>Copy the generated client ID and client secret to your .env file</li>
        </ol>
        
        <h2>Generated OAuth URL</h2>
        <p>Your OAuth URL would be (if environment variables are set correctly):</p>
        <div class="code">
            {get_google_oauth_url() if client_id and redirect_uri else "Cannot generate URL due to missing configuration"}
        </div>
        
        <h2>Common Issues</h2>
        <ul>
            <li><strong>Missing redirect_uri</strong>: Make sure GOOGLE_REDIRECT_URI is set in your .env file</li>
            <li><strong>URI mismatch</strong>: The redirect URI in your code must exactly match what's configured in Google Console</li>
            <li><strong>Environment variables not loaded</strong>: Make sure your .env file is being loaded properly</li>
            <li><strong>Invalid client_id</strong>: Verify your client ID in the Google Cloud Console</li>
        </ul>
    </body>
    </html>
    """

@router.get("/test-page", response_class=HTMLResponse)
async def auth_test_page():
    """
    A simple test page for authentication flows.
    
    Returns:
        HTML page with test links
    """
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Auth Test Page</title>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; padding: 20px; max-width: 800px; margin: 0 auto; }
            h1 { color: #333; }
            .card { border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin-bottom: 20px; }
            .button { display: inline-block; padding: 10px 15px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 4px; margin-right: 10px; }
            .warning { background-color: #fff3cd; border-color: #ffeeba; color: #856404; padding: 10px; border-radius: 4px; margin-bottom: 20px; }
            code { background-color: #f5f5f5; padding: 2px 4px; border-radius: 4px; font-family: monospace; }
        </style>
    </head>
    <body>
        <h1>Authentication Test Page</h1>
        
        <div class="warning">
            <strong>Note:</strong> This page is for testing purposes only. Use it to diagnose authentication issues.
        </div>
        
        <div class="card">
            <h2>Google OAuth Test</h2>
            <p>Click the button below to test the Google OAuth flow:</p>
            <a href="/api/auth/login/google" class="button">Login with Google</a>
            <a href="/api/auth/login/google?debug=true" class="button">Login with Debug Info</a>
        </div>
        
        <div class="card">
            <h2>Frontend Integration</h2>
            <p>For frontend integration, make a request to:</p>
            <code>GET /api/auth/login/google</code>
            <p>Your frontend should handle the redirect to Google's authentication page.</p>
        </div>
        
        <div class="card">
            <h2>Debugging Tools</h2>
            <p>Use these tools to diagnose authentication issues:</p>
            <a href="/api/auth/diagnostic" class="button">OAuth Diagnostic</a>
        </div>
        
        <div class="card">
            <h2>How Google OAuth Works</h2>
            <ol>
                <li>User clicks "Login with Google" on your frontend</li>
                <li>Frontend redirects to <code>/api/auth/login/google</code></li>
                <li>Backend redirects to Google's OAuth page</li>
                <li>User authenticates with Google</li>
                <li>Google redirects back to <code>/api/auth/callback/google</code> with a code</li>
                <li>Backend exchanges code for token and authenticates user</li>
                <li>Backend redirects to frontend with success/failure</li>
            </ol>
        </div>
    </body>
    </html>
    """ 