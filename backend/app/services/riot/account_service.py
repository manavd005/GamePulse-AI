"""
Riot Account Service Module.

Provides business logic for resolving Riot IDs (gameName#tagLine) and PUUID lookups
using the Riot Account-V1 API. Maps raw JSON to AccountDTO models.
"""

import logging
from typing import Optional

from app.core.constants import (
    ACCOUNT_BY_PUUID_ENDPOINT,
    ACCOUNT_BY_RIOT_ID_ENDPOINT,
    PLATFORM_TO_REGION_MAP,
    REGION_ASIA,
)
from app.core.exceptions import RiotAPIException, ServiceError
from app.schemas.account import AccountDTO
from app.services.riot_client import RiotClient

logger = logging.getLogger("gamepulse.account_service")


class AccountService:
    """
    Service layer for Riot Account-V1 operations.

    Handles player profile resolution and PUUID lookups. Communicates strictly
    through the injected RiotClient.
    """

    def __init__(self, riot_client: Optional[RiotClient] = None) -> None:
        """
        Initializes the AccountService.

        Args:
            riot_client (RiotClient, optional): Riot API HTTP client instance.
        """
        self.client = riot_client or RiotClient()

    def _resolve_regional_routing(self, region: str) -> str:
        """
        Maps platform region codes (e.g., 'ap', 'na') to Riot regional routing clusters
        (e.g., 'asia', 'americas') required by Account-V1.
        """
        r_lower = region.lower()
        if r_lower in PLATFORM_TO_REGION_MAP:
            return PLATFORM_TO_REGION_MAP[r_lower]
        # Return as is if already a regional cluster (e.g. 'asia', 'americas', 'europe')
        return r_lower

    def get_account_by_riot_id(
        self,
        game_name: str,
        tag_line: str,
        region: Optional[str] = None,
    ) -> AccountDTO:
        """
        Fetches Riot Account info by game name and tag line (e.g. "TenZ" # "SEN").

        Args:
            game_name (str): In-game player name.
            tag_line (str): In-game tag line without '#'.
            region (str, optional): Target platform or regional cluster code.

        Returns:
            AccountDTO: Validated player account data model.

        Raises:
            ServiceError: If account resolution fails.
        """
        target_region = self._resolve_regional_routing(region or self.client.default_region)
        endpoint = ACCOUNT_BY_RIOT_ID_ENDPOINT.format(
            game_name=game_name,
            tag_line=tag_line,
        )

        logger.info(f"Resolving Riot ID '{game_name}#{tag_line}' on region '{target_region}'")
        try:
            raw_data = self.client.get(endpoint, region=target_region)
            return AccountDTO.model_validate(raw_data)
        except RiotAPIException as err:
            logger.error(f"Failed to lookup Riot ID '{game_name}#{tag_line}': {err}")
            raise ServiceError(f"Account resolution failed for '{game_name}#{tag_line}': {str(err)}") from err

    def get_account_by_puuid(
        self,
        puuid: str,
        region: Optional[str] = None,
    ) -> AccountDTO:
        """
        Fetches Riot Account info by player PUUID.

        Args:
            puuid (str): Encrypted PUUID string.
            region (str, optional): Target platform or regional cluster code.

        Returns:
            AccountDTO: Validated player account data model.

        Raises:
            ServiceError: If account resolution fails.
        """
        target_region = self._resolve_regional_routing(region or self.client.default_region)
        endpoint = ACCOUNT_BY_PUUID_ENDPOINT.format(puuid=puuid)

        logger.info(f"Resolving PUUID '{puuid}' on region '{target_region}'")
        try:
            raw_data = self.client.get(endpoint, region=target_region)
            return AccountDTO.model_validate(raw_data)
        except RiotAPIException as err:
            logger.error(f"Failed to lookup PUUID '{puuid}': {err}")
            raise ServiceError(f"PUUID resolution failed for '{puuid}': {str(err)}") from err
