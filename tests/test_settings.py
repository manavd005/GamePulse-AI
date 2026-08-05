"""
Unit tests for modular Pydantic Settings management (app.core.settings).
"""

import os
import sys
from pathlib import Path
import unittest

backend_path = Path(__file__).resolve().parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.core.exceptions import ConfigError
from app.core.settings import settings, SecuritySettings


class TestSettings(unittest.TestCase):
    """Tests for application modular settings configuration and validation."""

    def test_settings_loaded(self) -> None:
        """Verifies settings sub-configurations are initialized."""
        self.assertIsNotNone(settings.security.SECRET_KEY)
        self.assertIsNotNone(settings.riot.RIOT_API_KEY)
        self.assertIsNotNone(settings.db.DATABASE_URL)

    def test_mandatory_secret_key(self) -> None:
        """Verifies that an empty or missing SECRET_KEY raises ConfigError."""
        with self.assertRaises(ConfigError):
            SecuritySettings(SECRET_KEY="")

        with self.assertRaises(ConfigError):
            SecuritySettings(SECRET_KEY="short")

    def test_settings_types(self) -> None:
        """Verifies type definitions across sub-settings."""
        self.assertIsInstance(settings.riot.RIOT_REQUEST_TIMEOUT, float)
        self.assertIsInstance(settings.riot.RIOT_MAX_RETRIES, int)
        self.assertIsInstance(settings.app.ENVIRONMENT, str)


if __name__ == "__main__":
    unittest.main()
