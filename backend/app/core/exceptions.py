"""
Core Application Exceptions Hierarchy.

Defines domain-specific exception types for Riot API interactions, system settings,
and service business logic errors.
"""

from typing import Optional


class GamePulseException(Exception):
    """Base exception for all custom exceptions within GamePulse AI."""
    pass


class ConfigError(GamePulseException):
    """Raised when application settings are missing or invalid."""
    pass


class RiotAPIException(GamePulseException):
    """Base exception for HTTP interactions with Riot Games API."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class RiotAuthenticationError(RiotAPIException):
    """HTTP 401 / 403: Invalid, missing, or expired Riot API Key."""
    pass


class RiotNotFoundError(RiotAPIException):
    """HTTP 404: Requested player, match, or resource not found."""
    pass


class RiotRateLimitError(RiotAPIException):
    """HTTP 429: Rate limit exceeded."""

    def __init__(self, message: str, retry_after: int = 1, response_body: Optional[str] = None) -> None:
        super().__init__(message, status_code=429, response_body=response_body)
        self.retry_after = retry_after


class RiotServerError(RiotAPIException):
    """HTTP 5xx: Riot API internal server error."""
    pass


class ServiceError(GamePulseException):
    """Base exception for errors originating in the service layer."""
    pass
