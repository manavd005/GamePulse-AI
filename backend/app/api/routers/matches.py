"""
Match Telemetry API Router Module.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_match_service
from app.schemas.match import MatchDetailsDTO, MatchlistDTO
from app.services.riot.match_service import MatchService

router = APIRouter(prefix="/matches", tags=["Matches"])


@router.get("/player/{puuid}", response_model=MatchlistDTO, summary="Get Match History by Player PUUID")
def get_matchlist_by_puuid(
    puuid: str,
    region: Optional[str] = Query(default=None, description="Platform region code"),
    match_service: MatchService = Depends(get_match_service),
) -> MatchlistDTO:
    """Retrieve recent match history entries for a given player PUUID."""
    return match_service.get_matchlist_by_puuid(puuid=puuid, region=region)


@router.get("/{match_id}", response_model=MatchDetailsDTO, summary="Get Detailed Match Telemetry")
def get_match_details(
    match_id: str,
    region: Optional[str] = Query(default=None, description="Platform region code"),
    match_service: MatchService = Depends(get_match_service),
) -> MatchDetailsDTO:
    """Retrieve full match telemetry breakdown by match ID."""
    return match_service.get_match_details(match_id=match_id, region=region)
