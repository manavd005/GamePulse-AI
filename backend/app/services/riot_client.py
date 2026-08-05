"""
Backwards-compatibility alias for RiotClient.
"""

from app.clients.riot_client import (
    RiotClient,
    RiotAPIException,
    RiotAuthenticationError,
    RiotNotFoundError,
    RiotRateLimitError,
    RiotServerError,
)

__all__ = [
    "RiotClient",
    "RiotAPIException",
    "RiotAuthenticationError",
    "RiotNotFoundError",
    "RiotRateLimitError",
    "RiotServerError",
]
