"""
Valorant Status Service Module.

Provides business logic for querying platform status and health endpoints
via VAL-Status-V1 API. Maps status payloads to Pydantic PlatformStatusDTO models.
"""

import logging
from typing import Optional

from app.core.constants import VAL_STATUS_ENDPOINT
from app.core.exceptions import RiotAPIException, ServiceError
from app.schemas.common import HealthCheckResult
from app.schemas.status import PlatformStatusDTO
from app.services.riot_client import RiotClient

logger = logging.getLogger("gamepulse.status_service")


class StatusService:
    """
    Service layer for Valorant Platform Status operations.

    Handles health checks and platform status queries. Communicates strictly
    through the injected RiotClient.
    """

    def __init__(self, riot_client: Optional[RiotClient] = None) -> None:
        """
        Initializes the StatusService.

        Args:
            riot_client (RiotClient, optional): Riot API HTTP client instance.
        """
        self.client = riot_client or RiotClient()

    def get_platform_status(self, region: Optional[str] = None) -> PlatformStatusDTO:
        """
        Queries platform operational status for a target region.

        Args:
            region (str, optional): Target platform region code. Defaults to client default region.

        Returns:
            PlatformStatusDTO: Parsed platform status model.

        Raises:
            ServiceError: If status query fails.
        """
        target_region = region or self.client.default_region
        logger.info(f"Querying platform status for region '{target_region}'")

        try:
            raw_data = self.client.get(VAL_STATUS_ENDPOINT, region=target_region)
            p_id = raw_data.get("id", target_region.upper())
            p_name = raw_data.get("name", f"Valorant {target_region.upper()}")
            locales = raw_data.get("locales", [])
            incidents = raw_data.get("incidents", [])
            m_status = raw_data.get("maintenance_status", "operational")

            return PlatformStatusDTO(
                id=p_id,
                name=p_name,
                locales=locales,
                maintenance_status=m_status,
                incidents=incidents,
                raw_data=raw_data,
            )

        except RiotAPIException as err:
            logger.error(f"Failed to retrieve platform status for '{target_region}': {err}")
            raise ServiceError(f"Status check failed for region '{target_region}': {str(err)}") from err

    def check_health(self, region: Optional[str] = None) -> HealthCheckResult:
        """
        Executes a lightweight health check probe against the Riot API.

        Args:
            region (str, optional): Target platform region.

        Returns:
            HealthCheckResult: Health assessment model.
        """
        target_region = region or self.client.default_region
        try:
            status_dto = self.get_platform_status(region=target_region)
            return HealthCheckResult(
                status="healthy",
                region=target_region,
                details={
                    "platform_id": status_dto.id,
                    "maintenance_status": status_dto.maintenance_status,
                    "incident_count": len(status_dto.incidents),
                },
            )
        except Exception as err:
            logger.warning(f"Health check probe failed for region '{target_region}': {err}")
            return HealthCheckResult(
                status="degraded",
                region=target_region,
                details={"error": str(err)},
            )
