"""
Centralized FastAPI Exception Handlers Module.

Registers global exception handlers for mapping domain exceptions to HTTP JSON responses.
Uses a reusable helper function to avoid repeated JSONResponse construction.
"""

import logging
from typing import Dict, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    ConfigError,
    GamePulseException,
    RiotAuthenticationError,
    RiotNotFoundError,
    RiotRateLimitError,
    RiotServerError,
    ServiceError,
)
from app.schemas.common import ApiError

logger = logging.getLogger("gamepulse.exceptions")


def _build_error_response(
    status_code: int,
    message: str,
    details: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
) -> JSONResponse:
    """Helper function to construct standardized ApiError JSON responses."""
    error_payload = ApiError(
        status_code=status_code,
        message=message,
        details=details,
    )
    return JSONResponse(
        status_code=status_code,
        content=error_payload.model_dump(),
        headers=headers,
    )


def register_exception_handlers(app) -> None:
    """Registers exception handlers with the FastAPI application instance."""

    @app.exception_handler(RiotAuthenticationError)
    async def riot_auth_exception_handler(request: Request, exc: RiotAuthenticationError) -> JSONResponse:
        logger.warning(f"Authentication Error: {exc}")
        return _build_error_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Riot API authentication failed. Verify API key credentials.",
            details=str(exc),
        )

    @app.exception_handler(RiotNotFoundError)
    async def riot_not_found_exception_handler(request: Request, exc: RiotNotFoundError) -> JSONResponse:
        logger.info(f"Not Found Error: {exc}")
        return _build_error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            message="Requested Riot resource was not found.",
            details=str(exc),
        )

    @app.exception_handler(RiotRateLimitError)
    async def riot_rate_limit_exception_handler(request: Request, exc: RiotRateLimitError) -> JSONResponse:
        logger.warning(f"Rate Limit Error: {exc}")
        return _build_error_response(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            message=f"Riot API rate limit exceeded. Retry after {exc.retry_after} seconds.",
            details=str(exc),
            headers={"Retry-After": str(exc.retry_after)},
        )

    @app.exception_handler(RiotServerError)
    async def riot_server_exception_handler(request: Request, exc: RiotServerError) -> JSONResponse:
        logger.error(f"Riot Server Error: {exc}")
        return _build_error_response(
            status_code=status.HTTP_502_BAD_GATEWAY,
            message="Upstream Riot API server error.",
            details=str(exc),
        )

    @app.exception_handler(ServiceError)
    async def service_exception_handler(request: Request, exc: ServiceError) -> JSONResponse:
        logger.error(f"Service Error: {exc}")
        return _build_error_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Domain service operation failed.",
            details=str(exc),
        )

    @app.exception_handler(ConfigError)
    async def config_exception_handler(request: Request, exc: ConfigError) -> JSONResponse:
        logger.critical(f"Configuration Error: {exc}")
        return _build_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Server configuration error.",
            details=str(exc),
        )

    @app.exception_handler(GamePulseException)
    async def gamepulse_generic_exception_handler(request: Request, exc: GamePulseException) -> JSONResponse:
        logger.error(f"GamePulse Exception: {exc}")
        return _build_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Internal application error.",
            details=str(exc),
        )
