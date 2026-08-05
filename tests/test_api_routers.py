"""
Integration tests for FastAPI Routers (app.api.routers).
"""

import sys
from pathlib import Path
import unittest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

backend_path = Path(__file__).resolve().parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from main import app
from app.api.dependencies import get_account_service, get_status_service
from app.schemas.account import AccountDTO
from app.schemas.common import HealthCheckResult


class TestApiRouters(unittest.TestCase):
    """Tests for FastAPI HTTP routers and status endpoints."""

    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_root_endpoint(self) -> None:
        """Verifies root endpoint status payload."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(json_data["status"], "online")
        self.assertIn("name", json_data)

    def test_health_check_endpoint(self) -> None:
        """Verifies /api/v1/health endpoint with mocked StatusService."""
        mock_status_svc = MagicMock()
        mock_status_svc.check_health.return_value = HealthCheckResult(
            status="healthy",
            region="ap",
            details={"platform_id": "AP"},
        )
        app.dependency_overrides[get_status_service] = lambda: mock_status_svc

        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "healthy")

        app.dependency_overrides.clear()

    def test_player_search_endpoint(self) -> None:
        """Verifies /api/v1/players/search endpoint with mocked AccountService."""
        mock_account_svc = MagicMock()
        mock_account_svc.get_account_by_riot_id.return_value = AccountDTO(
            puuid="mock-puuid-12345",
            gameName="TenZ",
            tagLine="SEN",
        )
        app.dependency_overrides[get_account_service] = lambda: mock_account_svc

        response = self.client.get("/api/v1/players/search?game_name=TenZ&tag_line=SEN")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["gameName"], "TenZ")
        self.assertEqual(data["puuid"], "mock-puuid-12345")

        app.dependency_overrides.clear()


if __name__ == "__main__":
    unittest.main()
