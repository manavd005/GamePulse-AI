"""
Unit tests for low-level RiotClient (app.services.riot_client).
"""

import sys
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

backend_path = Path(__file__).resolve().parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.core.exceptions import (
    RiotAuthenticationError,
    RiotNotFoundError,
    RiotRateLimitError,
)
from app.services.riot_client import RiotClient


class TestRiotClient(unittest.TestCase):
    """Tests for RiotClient HTTP transport, headers, and retry logic."""

    def setUp(self) -> None:
        self.dummy_key = "RGAPI-TEST-KEY-12345"
        self.client = RiotClient(api_key=self.dummy_key, default_region="ap", max_retries=2, backoff_factor=0.01)

    def test_authentication_header_injected(self) -> None:
        """Verifies X-Riot-Token is injected into session headers."""
        self.assertEqual(self.client._session.headers.get("X-Riot-Token"), self.dummy_key)

    @patch("requests.Session.request")
    def test_successful_get_request(self, mock_request: MagicMock) -> None:
        """Verifies successful GET request parsing."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "AP", "name": "Asia Pacific"}
        mock_request.return_value = mock_response

        result = self.client.get("/val/status/v1/platform-data", region="ap")
        self.assertEqual(result["id"], "AP")
        self.assertEqual(result["name"], "Asia Pacific")

    @patch("requests.Session.request")
    def test_401_authentication_error(self, mock_request: MagicMock) -> None:
        """Verifies RiotAuthenticationError is raised on 401/403."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Forbidden"
        mock_request.return_value = mock_response

        with self.assertRaises(RiotAuthenticationError):
            self.client.get("/val/status/v1/platform-data")

    @patch("requests.Session.request")
    def test_404_not_found_error(self, mock_request: MagicMock) -> None:
        """Verifies RiotNotFoundError is raised on 404."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_request.return_value = mock_response

        with self.assertRaises(RiotNotFoundError):
            self.client.get("/riot/account/v1/accounts/by-riot-id/NonExistent/0000")

    @patch("requests.Session.request")
    @patch("time.sleep", return_value=None)
    def test_429_retry_logic(self, mock_sleep: MagicMock, mock_request: MagicMock) -> None:
        """Verifies 429 rate limit triggers retries with Retry-After sleep."""
        # 1st attempt returns 429, 2nd attempt returns 200
        mock_429 = MagicMock()
        mock_429.status_code = 429
        mock_429.headers = {"Retry-After": "1"}
        mock_429.text = "Rate Limit Exceeded"

        mock_200 = MagicMock()
        mock_200.status_code = 200
        mock_200.json.return_value = {"status": "ok"}

        mock_request.side_effect = [mock_429, mock_200]

        result = self.client.get("/val/status/v1/platform-data")
        self.assertEqual(result, {"status": "ok"})
        self.assertEqual(mock_request.call_count, 2)
        mock_sleep.assert_called_with(1)


if __name__ == "__main__":
    unittest.main()