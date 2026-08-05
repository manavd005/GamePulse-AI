"""
Valorant Match Service Module.

Provides business logic for retrieving match history lists and match details
from the Riot VAL-Match-V1 API. Maps responses to Pydantic Match models.
"""

import logging
from typing import Optional

from app.core.constants import VAL_MATCH_BY_ID_ENDPOINT, VAL_MATCHLIST_BY_PUUID_ENDPOINT
from app.core.exceptions import RiotAPIException, ServiceError
from app.schemas.match import MatchDetailsDTO, MatchEntryDTO, MatchlistDTO
from app.services.riot_client import RiotClient

logger = logging.getLogger("gamepulse.match_service")


class MatchService:
    """
    Service layer for Valorant Match-V1 operations.

    Handles match history queries and match detail ingestion. Communicates strictly
    through the injected RiotClient.
    """

    def __init__(self, riot_client: Optional[RiotClient] = None) -> None:
        """
        Initializes the MatchService.

        Args:
            riot_client (RiotClient, optional): Riot API HTTP client instance.
        """
        self.client = riot_client or RiotClient()

    def get_matchlist_by_puuid(
        self,
        puuid: str,
        region: Optional[str] = None,
    ) -> MatchlistDTO:
        """
        Retrieves recent match history items for a given player PUUID.

        Args:
            puuid (str): Encrypted player PUUID string.
            region (str, optional): Target platform region code (e.g. 'ap', 'na').

        Returns:
            MatchlistDTO: Validated match history collection model.

        Raises:
            ServiceError: If retrieving match history fails.
        """
        target_region = region or self.client.default_region
        endpoint = VAL_MATCHLIST_BY_PUUID_ENDPOINT.format(puuid=puuid)

        logger.info(f"Fetching matchlist for PUUID '{puuid}' on region '{target_region}'")
        try:
            raw_data = self.client.get(endpoint, region=target_region)
            
            # Normalize response payload if wrapped or raw list
            history_items = []
            if isinstance(raw_data, dict):
                raw_history = raw_data.get("history", raw_data.get("matches", []))
                for item in raw_history:
                    if isinstance(item, dict):
                        history_items.append(MatchEntryDTO.model_validate(item))
                    elif isinstance(item, str):
                        history_items.append(MatchEntryDTO(matchId=item))

            return MatchlistDTO(puuid=puuid, history=history_items)

        except RiotAPIException as err:
            logger.error(f"Failed to fetch matchlist for PUUID '{puuid}': {err}")
            raise ServiceError(f"Matchlist query failed for PUUID '{puuid}': {str(err)}") from err

    def get_match_details(
        self,
        match_id: str,
        region: Optional[str] = None,
    ) -> MatchDetailsDTO:
        """
        Retrieves full match telemetry and statistics by match ID.

        Args:
            match_id (str): Unique match identifier string.
            region (str, optional): Target platform region code.

        Returns:
            MatchDetailsDTO: Validated match details model containing metadata, player stats, and round telemetry.

        Raises:
            ServiceError: If match detail retrieval fails.
        """
        target_region = region or self.client.default_region
        endpoint = VAL_MATCH_BY_ID_ENDPOINT.format(match_id=match_id)

        logger.info(f"Fetching match details for match ID '{match_id}' on region '{target_region}'")
        try:
            raw_data = self.client.get(endpoint, region=target_region)
            match_info = raw_data.get("matchInfo", {})
            players = raw_data.get("players", [])
            teams = raw_data.get("teams", [])

            return MatchDetailsDTO(
                matchId=match_id,
                matchInfo=match_info,
                players=players,
                teams=teams,
                raw_data=raw_data,
            )

        except RiotAPIException as err:
            logger.error(f"Failed to fetch match details for '{match_id}': {err}")
            raise ServiceError(f"Match details query failed for match ID '{match_id}': {str(err)}") from err
