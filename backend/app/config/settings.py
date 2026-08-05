"""
Deprecated Settings module. Redirects to app.core.settings.
"""

from app.core.settings import settings, Settings
from app.core.exceptions import ConfigError

__all__ = ["settings", "Settings", "ConfigError"]
