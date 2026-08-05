"""
Health & Status API Router Module.
"""

from typing import Optional
from fastapi import APIRouter, Depends

from app.api.dependencies import get_status_service
from app.schemas.common import HealthCheckResult
from app.schemas.status import PlatformStatusDTO
from app.services.riot.status_service import StatusService

router = APIRouter(prefix="/health", tags=["Health & Status"])


@router.get("", response_model=HealthCheckResult, summary="Check System Health")
def check_health(
    region: Optional[str] = None,
    status_service: StatusService = Depends(get_status_service),
) -> HealthCheckResult:
    """Probes system health status and Riot API connectivity."""
    return status_service.check_health(region=region)


@router.get("/platform", response_model=PlatformStatusDTO, summary="Get Valorant Platform Status")
def get_platform_status(
    region: Optional[str] = None,
    status_service: StatusService = Depends(get_status_service),
) -> PlatformStatusDTO:
    """Retrieves operational status of Valorant platform servers for a target region."""
    return status_service.get_platform_status(region=region)
