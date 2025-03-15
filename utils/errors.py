"""
Custom error classes for AIdentity.ai backend.

This module defines custom exceptions used throughout the application.
"""
from typing import Any, Dict, Optional

from fastapi import HTTPException, status


class BaseAPIError(HTTPException):
    """
    Base class for all API errors.
    
    Attributes:
        status_code: HTTP status code
        detail: Error message
        error_code: Machine-readable error code
    """
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: str,
        headers: Optional[Dict[str, Any]] = None
    ):
        self.error_code = error_code
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class DatabaseError(BaseAPIError):
    """Exception raised for database-related errors."""
    def __init__(self, detail: str, error_code: str = "database_error"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code=error_code
        )


class NotFoundError(BaseAPIError):
    """Exception raised when a resource is not found."""
    def __init__(self, detail: str, error_code: str = "not_found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code=error_code
        )


class ValidationError(BaseAPIError):
    """Exception raised for validation errors."""
    def __init__(self, detail: str, error_code: str = "validation_error"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code=error_code
        )


class AuthenticationError(BaseAPIError):
    """Exception raised for authentication errors."""
    def __init__(self, detail: str, error_code: str = "authentication_error"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code=error_code
        )


class AuthorizationError(BaseAPIError):
    """Exception raised for authorization errors."""
    def __init__(self, detail: str, error_code: str = "authorization_error"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code=error_code
        )


class AgentFailureError(BaseAPIError):
    """Exception raised when an AI agent fails to complete a task."""
    def __init__(self, detail: str, error_code: str = "agent_failure"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code=error_code
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