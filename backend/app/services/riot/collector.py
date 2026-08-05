"""
Riot Data Collector Module.

Orchestrates multi-service player and match telemetry collection.
Persists raw JSON payloads to organized directories under data/raw/players/ folder
and optionally saves structured entities via database repository interfaces.
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.exceptions import ServiceError
from app.models.match import MatchModel
from app.models.player import PlayerModel
from app.repositories.match_repository import IMatchRepository
from app.repositories.player_repository import IPlayerRepository
from app.schemas.account import AccountDTO
from app.schemas.match import MatchDetailsDTO, MatchlistDTO
from app.services.riot.account_service import AccountService
from app.services.riot.match_service import MatchService
from app.services.riot.status_service import StatusService

logger = logging.getLogger("gamepulse.collector")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
DEFAULT_RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw" / "players"


class RiotDataCollector:
    """
    Coordinator service for querying Riot API data and storing raw JSON telemetry.
    Supports constructor dependency injection for services and repositories.
    """

    def __init__(
        self,
        account_service: AccountService,
        match_service: MatchService,
        status_service: StatusService,
        player_repo: Optional[IPlayerRepository] = None,
        match_repo: Optional[IMatchRepository] = None,
        raw_data_dir: Optional[Path] = None,
    ) -> None:
        """
        Initializes the Data Collector with injected dependencies.

        Args:
            account_service (AccountService): Account service instance.
            match_service (MatchService): Match service instance.
            status_service (StatusService): Status service instance.
            player_repo (IPlayerRepository, optional): Player repository instance.
            match_repo (IMatchRepository, optional): Match repository instance.
            raw_data_dir (Path, optional): Target root directory for persisting raw telemetry.
        """
        self.account_service = account_service
        self.match_service = match_service
        self.status_service = status_service
        self.player_repo = player_repo
        self.match_repo = match_repo
        self.raw_data_dir = raw_data_dir or DEFAULT_RAW_DATA_DIR

    @staticmethod
    def _sanitize_folder_name(name: str) -> str:
        """Sanitizes game names and tag lines for safe filesystem folder creation."""
        return re.sub(r"[^\w\-.]", "_", name.strip())

    def search_player(
        self,
        game_name: str,
        tag_line: str,
        region: str = "ap",
    ) -> AccountDTO:
        """
        Looks up a player by game name and tag line, persisting to repository if present.

        Args:
            game_name (str): Player Riot ID name.
            tag_line (str): Player Riot ID tag.
            region (str): Target platform or regional cluster code.

        Returns:
            AccountDTO: Account details data transfer object.
        """
        logger.info(f"Collector searching player '{game_name}#{tag_line}' [Region: {region}]")
        account = self.account_service.get_account_by_riot_id(game_name, tag_line, region=region)

        # Save to player repository if available
        if self.player_repo:
            player_entity = PlayerModel(
                puuid=account.puuid,
                game_name=account.gameName,
                tag_line=account.tagLine,
                region=region,
            )
            self.player_repo.add(player_entity)
            logger.info(f"Persisted player '{game_name}#{tag_line}' to database repository.")

        return account

    def get_match_ids(self, puuid: str, region: str = "ap") -> List[str]:
        """Retrieves match ID strings for a player's PUUID."""
        logger.info(f"Collector retrieving match IDs for PUUID '{puuid}'")
        matchlist_dto: MatchlistDTO = self.match_service.get_matchlist_by_puuid(puuid, region=region)
        return [item.matchId for item in matchlist_dto.history]

    def get_match_details(
        self,
        match_id: str,
        region: str = "ap",
        puuid: Optional[str] = None,
    ) -> MatchDetailsDTO:
        """
        Retrieves full match telemetry for a specific match ID and persists to repository if present.

        Args:
            match_id (str): Unique match identifier string.
            region (str): Target platform region code.
            puuid (str, optional): Target player PUUID.

        Returns:
            MatchDetailsDTO: Detailed match data transfer object.
        """
        logger.info(f"Collector retrieving match details for match ID '{match_id}'")
        match_details = self.match_service.get_match_details(match_id, region=region)

        if self.match_repo:
            match_entity = MatchModel(
                match_id=match_id,
                puuid=puuid,
                queue_id=match_details.matchInfo.get("queueId"),
                game_start_time=match_details.matchInfo.get("gameStartMillis"),
                raw_json=match_details.raw_data or match_details.model_dump(),
            )
            self.match_repo.add(match_entity)
            logger.info(f"Persisted match '{match_id}' to database repository.")

        return match_details

    def save_raw_json(self, data: Dict[str, Any], file_path: Path, overwrite: bool = False) -> Path:
        """Safely serializes and saves a dictionary to a JSON file."""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        if file_path.exists() and not overwrite:
            logger.info(f"File '{file_path}' already exists. Skipping overwrite.")
            return file_path

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Successfully saved raw JSON to '{file_path}'")
        return file_path

    def collect_player_data(
        self,
        game_name: str,
        tag_line: str,
        region: str = "ap",
        max_matches: int = 5,
    ) -> Dict[str, Any]:
        """
        High-level orchestration method fetching player account info, recent matches,
        and match details, persisting to disk and database repository.
        """
        safe_name = self._sanitize_folder_name(f"{game_name}_{tag_line}")
        player_dir = self.raw_data_dir / safe_name
        matches_dir = player_dir / "matches"

        account = self.search_player(game_name, tag_line, region=region)
        account_file = player_dir / "account.json"
        self.save_raw_json(account.model_dump(), account_file, overwrite=True)

        match_ids = self.get_match_ids(account.puuid, region=region)
        saved_matches = []

        for m_id in match_ids[:max_matches]:
            try:
                m_details = self.get_match_details(m_id, region=region, puuid=account.puuid)
                m_file = matches_dir / f"{m_id}.json"
                self.save_raw_json(m_details.raw_data or m_details.model_dump(), m_file)
                saved_matches.append(m_id)
            except ServiceError as err:
                logger.warning(f"Failed to ingest match '{m_id}' for player '{game_name}': {err}")

        return {
            "player": f"{game_name}#{tag_line}",
            "puuid": account.puuid,
            "player_dir": str(player_dir),
            "matches_collected": len(saved_matches),
            "match_ids": saved_matches,
        }
