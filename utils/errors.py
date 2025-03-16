"""
Custom error classes for AIdentity.ai backend.

This module defines custom exceptions used throughout the application.
"""
from typing import Any, Dict, Optional

from fastapi import HTTPException, status


class BaseAPIError(Exception):
    """Base class for all API errors."""
    def __init__(
        self, 
        detail: str, 
        status_code: int = 500, 
        error_code: str = "internal_error"
    ):
        """
        Initialize the error.
        
        Args:
            detail: Human-readable error description
            status_code: HTTP status code
            error_code: Machine-readable error code
        """
        self.detail = detail
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.detail)


class DatabaseError(BaseAPIError):
    """Exception raised for database-related errors."""
    def __init__(self, detail: str, error_code: str = "database_error"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=error_code
        )


class NotFoundError(BaseAPIError):
    """Exception raised when a resource is not found."""
    def __init__(self, detail: str, error_code: str = "not_found"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code=error_code
        )


class ValidationError(BaseAPIError):
    """Error for invalid input data."""
    def __init__(self, detail: str):
        super().__init__(
            detail=detail,
            status_code=400,
            error_code="validation_error"
        )


class AuthenticationError(BaseAPIError):
    """Error for authentication failures."""
    def __init__(self, detail: str):
        super().__init__(
            detail=detail,
            status_code=401,
            error_code="authentication_error"
        )


class AuthorizationError(BaseAPIError):
    """Error for authorization failures."""
    def __init__(self, detail: str):
        super().__init__(
            detail=detail,
            status_code=403,
            error_code="authorization_error"
        )


class AgentFailureError(BaseAPIError):
    """Error for AI agent failures."""
    def __init__(self, detail: str):
        super().__init__(
            detail=detail,
            status_code=500,
            error_code="agent_failure"
        )


class ExternalAPIError(BaseAPIError):
    """Exception raised when an external API call fails."""
    def __init__(self, detail: str, error_code: str = "external_api_error"):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=detail,
            error_code=error_code
        )


class MediaProcessingError(BaseAPIError):
    """Exception raised when media processing fails."""
    def __init__(self, detail: str, error_code: str = "media_processing_error"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code=error_code
        )


class RateLimitError(BaseAPIError):
    """Exception raised when rate limit is exceeded."""
    def __init__(self, detail: str, error_code: str = "rate_limit_exceeded"):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            error_code=error_code
        ) 