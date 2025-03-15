# AIdentity.ai Backend

Backend API for AIdentity.ai, an AI-driven app for content creation, featuring AI agents, web crawling, media processing, and autonomous posting.

## Tech Stack

- **Back End**: FastAPI, Pymongo, Redis with RQ
- **Database**: MongoDB
- **AI Agents**: LangChain, OpenAI GPT-3.5 Turbo, Gemini, Anthropic Claude 3.5 Sonnet
- **Web Crawling**: Crawl4AI
- **Media Processing**: FFmpeg, MoviePy, OpenCV
- **Monitoring**: Sentry, Prometheus, Grafana
- **Third-Party APIs**: OAuth Authentication, HeyGen, Eleven Labs, Twitter API, Reddit API

## Setup Instructions

### Prerequisites

- Python 3.9+
- MongoDB
- Redis
- FFmpeg (for media processing)

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/your-username/aidentity-backend.git
   cd aidentity-backend
   ```

2. Create a virtual environment:

   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:

   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

5. Create a `.env` file in the project root and configure your environment variables:

   ```
   # Development Mode (set to "false" in production)
   DEV_MODE=true

   # MongoDB Configuration
   MONGO_URI=mongodb://localhost:27017
   DB_NAME=aidentity

   # Redis Configuration
   REDIS_HOST=localhost
   REDIS_PORT=6379
   REDIS_DB=0

   # Authentication
   SECRET_KEY=your_secret_key_at_least_32_characters_long
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   GOOGLE_CLIENT_ID=your_google_client_id
   GOOGLE_CLIENT_SECRET=your_google_client_secret
   OAUTH_REDIRECT_URL=http://localhost:8000/api/auth/callback/google

   # AI API Keys
   OPENAI_API_KEY=your_openai_api_key
   ANTHROPIC_API_KEY=your_anthropic_api_key
   GOOGLE_API_KEY=your_google_api_key
   ```

### Setting Up Google OAuth

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project or select an existing one.
3. Navigate to "APIs & Services" > "Credentials".
4. Click "Create Credentials" and select "OAuth client ID".
5. Select "Web application" as the application type.
6. Add a name for your OAuth client.
7. Add the following authorized redirect URI:
   ```
   http://localhost:8000/api/auth/callback/google
   ```
8. Click "Create" to generate your client ID and client secret.
9. Copy the client ID and client secret to your `.env` file:
   ```
   GOOGLE_CLIENT_ID=your_google_client_id
   GOOGLE_CLIENT_SECRET=your_google_client_secret
   ```

### Running the Server

1. Start MongoDB and Redis:

   - MongoDB:
     ```bash
     mongod --dbpath /path/to/data/db
     ```
   - Redis:
     ```bash
     redis-server
     ```

2. Run the FastAPI server:

   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

3. Access the API documentation:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Authentication Endpoints

- **Google OAuth Login**: `/api/auth/login/google`
- **Google OAuth Callback**: `/api/auth/callback/google`
- **Get Current User**: `/api/auth/me`
- **Logout**: `/api/auth/logout`

### Development Mode

By default, the server runs in development mode, which disables database connections. To enable database connections, set `DEV_MODE=false` in your `.env` file.

## Project Structure

```
backend/
├── main.py                 # Entry point
├── requirements.txt        # Dependencies
├── .env                    # Environment variables
├── routers/                # Route definitions for API endpoints
│   ├── auth_router.py      # Authentication routes
├── services/               # Business logic services
│   ├── auth_service.py     # Authentication service
├── middleware/             # Middleware components
│   ├── auth_middleware.py  # Authentication middleware
├── agents/                 # AI agent logic and workflows
├── utils/                  # Utility functions
│   ├── auth.py             # Authentication utilities
│   ├── config.py           # Configuration utilities
│   ├── db.py               # Database utilities
│   ├── errors.py           # Error handling utilities
│   ├── oauth.py            # OAuth providers
├── media/                  # Media processing-specific logic
├── schemas/                # Pydantic models for data validation
├── workers/                # RQ background task definitions
└── tests/                  # Unit tests for all components
```

## API Documentation

The API documentation is available at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

Run tests using pytest:

```bash
pytest
```

## License

[MIT License](LICENSE)
