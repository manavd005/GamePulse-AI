"""
Unit tests for AccountService (app.services.riot.account_service).
"""

import sys
from pathlib import Path
import unittest
from unittest.mock import MagicMock

backend_path = Path(__file__).resolve().parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.core.exceptions import RiotAPIException, ServiceError
from app.schemas.account import AccountDTO
from app.services.riot.account_service import AccountService


class TestAccountService(unittest.TestCase):
    """Tests for AccountService business logic and Pydantic model mapping."""

    def setUp(self) -> None:
        self.mock_client = MagicMock()
        self.service = AccountService(riot_client=self.mock_client)

    def test_get_account_by_riot_id_success(self) -> None:
        """Verifies successful lookup of Riot ID returns a valid AccountDTO."""
        self.mock_client.default_region = "ap"
        self.mock_client.get.return_value = {
            "puuid": "mock-puuid-12345",
            "gameName": "TenZ",
            "tagLine": "SEN",
        }

        account = self.service.get_account_by_riot_id("TenZ", "SEN", region="ap")
        self.assertIsInstance(account, AccountDTO)
        self.assertEqual(account.puuid, "mock-puuid-12345")
        self.assertEqual(account.gameName, "TenZ")
        self.assertEqual(account.tagLine, "SEN")

        # Verify platform region "ap" was converted to regional cluster "asia" for Account-V1
        self.mock_client.get.assert_called_once_with(
            "/riot/account/v1/accounts/by-riot-id/TenZ/SEN",
            region="asia",
        )

    def test_get_account_by_riot_id_failure(self) -> None:
        """Verifies RiotAPIException is wrapped in ServiceError."""
        self.mock_client.default_region = "ap"
        self.mock_client.get.side_effect = RiotAPIException("Resource not found", status_code=404)

        with self.assertRaises(ServiceError):
            self.service.get_account_by_riot_id("Invalid", "0000")


if __name__ == "__main__":
    unittest.main()
