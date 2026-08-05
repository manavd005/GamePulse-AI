"""
Centralized Logging Configuration Module for GamePulse AI.
"""

import sys
import logging
from app.core.settings import settings


def setup_logging() -> None:
    """Configures structured logging across all GamePulse application modules."""
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )
