"""
GamePulse AI Backend Application Entry Point.

Configures logging, validates modular settings, initializes database schema,
registers custom exception handlers, and mounts FastAPI routers under /api/v1.
Enforces fail-fast startup behavior if database initialization encounters any error.
"""

import sys
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI

# Ensure backend directory is in sys.path for direct module execution (e.g. uvicorn backend.main:app)
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.settings import settings
from app.core.logging import setup_logging
from app.core.exceptions import ConfigError
from app.database.session import init_db
from app.api.exception_handlers import register_exception_handlers
from app.api.api_v1 import api_v1_router

# Setup structured logging before anything else
setup_logging()
logger = logging.getLogger("gamepulse.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI Lifespan Context Manager: Handles application startup and shutdown events."""
    logger.info("Initializing GamePulse AI Backend Services...")
    logger.info(f"Environment: '{settings.ENVIRONMENT}' | Log Level: '{settings.LOG_LEVEL}'")
    logger.info(f"Riot Default Region: '{settings.RIOT_DEFAULT_REGION}' | Timeout: {settings.RIOT_REQUEST_TIMEOUT}s")
    
    # Enforce Fail-Fast behavior: Re-raise exception if database initialization fails
    try:
        init_db()
    except Exception as err:
        logger.exception("Database initialization failed during startup. Aborting application launch.")
        raise

    logger.info("GamePulse AI Startup Sequence Completed Successfully.")
    yield
    logger.info("GamePulse AI Shutdown Completed.")


# Create FastAPI application instance
app = FastAPI(
    title=settings.app.PROJECT_NAME,
    version=settings.app.PROJECT_VERSION,
    description="AI-Powered VALORANT Player Analytics & Behaviour Prediction Platform API",
    lifespan=lifespan,
    debug=settings.app.DEBUG,
)

# Register Centralized Exception Handlers
register_exception_handlers(app)

# Mount API v1 Routers
app.include_router(api_v1_router, prefix="/api")


@app.get("/", summary="Root Status", tags=["Health & Status"])
def root_status():
    """Returns basic system description and version status."""
    return {
        "name": settings.app.PROJECT_NAME,
        "version": settings.app.PROJECT_VERSION,
        "status": "online",
        "docs_url": "/docs",
    }


def main() -> None:
    """CLI Entry Point for standalone verification."""
    logger.info("Running standalone backend initialization check...")
    logger.info(f"Settings validated: SECRET_KEY present, Default Region: '{settings.RIOT_DEFAULT_REGION}'")
    try:
        init_db()
    except Exception as err:
        logger.exception("Database initialization failed during CLI check.")
        raise
    logger.info("Initialization check complete.")


if __name__ == "__main__":
    main()
