"""
Unit tests for Database Repository layer (app.repositories).
"""

import sys
from pathlib import Path
import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

backend_path = Path(__file__).resolve().parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.database.session import Base
from app.models.player import PlayerModel
from app.models.match import MatchModel
from app.repositories.player_repository import SQLAlchemyPlayerRepository
from app.repositories.match_repository import SQLAlchemyMatchRepository


class TestRepositories(unittest.TestCase):
    """Tests for Player and Match repositories using an in-memory SQLite database."""

    def setUp(self) -> None:
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=self.engine)
        Session = sessionmaker(bind=self.engine)
        self.db = Session()
        self.player_repo = SQLAlchemyPlayerRepository(db_session=self.db)
        self.match_repo = SQLAlchemyMatchRepository(db_session=self.db)

    def tearDown(self) -> None:
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_player_repository_crud(self) -> None:
        """Verifies adding, retrieving, and listing players in PlayerRepository."""
        player = PlayerModel(
            puuid="test-puuid-12345",
            game_name="TenZ",
            tag_line="SEN",
            region="ap",
        )
        self.player_repo.add(player)

        retrieved = self.player_repo.get_by_id("test-puuid-12345")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.game_name, "TenZ")

        by_riot_id = self.player_repo.get_by_riot_id("TenZ", "SEN")
        self.assertIsNotNone(by_riot_id)
        self.assertEqual(by_riot_id.puuid, "test-puuid-12345")

    def test_match_repository_crud(self) -> None:
        """Verifies adding and listing matches in MatchRepository."""
        match = MatchModel(
            match_id="match-id-9999",
            puuid="test-puuid-12345",
            queue_id="competitive",
            game_start_time=1700000000000,
            raw_json={"map": "Ascent"},
        )
        self.match_repo.add(match)

        retrieved = self.match_repo.get_by_id("match-id-9999")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.queue_id, "competitive")

        matches = self.match_repo.list_by_puuid("test-puuid-12345")
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].match_id, "match-id-9999")


if __name__ == "__main__":
    unittest.main()
