"""
Player Management & Ingestion API Router Module.
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_account_service, get_collector_service
from app.core.constants import DEFAULT_COLLECT_MAX_MATCHES
from app.schemas.account import AccountDTO
from app.services.riot.account_service import AccountService
from app.services.riot.collector import RiotDataCollector

router = APIRouter(prefix="/players", tags=["Players"])


@router.get("/search", response_model=AccountDTO, summary="Search Player by Riot ID")
def search_player(
    game_name: str = Query(..., description="In-game Riot ID name (e.g. TenZ)"),
    tag_line: str = Query(..., description="In-game Riot ID tag (e.g. SEN)"),
    region: Optional[str] = Query(default=None, description="Platform region code (e.g. ap, na)"),
    account_service: AccountService = Depends(get_account_service),
) -> AccountDTO:
    """Look up player profile and PUUID by Riot ID (gameName#tagLine)."""
    return account_service.get_account_by_riot_id(game_name=game_name, tag_line=tag_line, region=region)


@router.get("/{puuid}", response_model=AccountDTO, summary="Get Player by PUUID")
def get_player_by_puuid(
    puuid: str,
    region: Optional[str] = Query(default=None, description="Platform region code"),
    account_service: AccountService = Depends(get_account_service),
) -> AccountDTO:
    """Retrieve player identity info by encrypted PUUID."""
    return account_service.get_account_by_puuid(puuid=puuid, region=region)


@router.post("/collect", summary="Ingest & Store Player Telemetry Data")
def collect_player_data(
    game_name: str = Query(..., description="In-game Riot ID name"),
    tag_line: str = Query(..., description="In-game Riot ID tag"),
    region: str = Query(default="ap", description="Target platform region"),
    max_matches: int = Query(default=DEFAULT_COLLECT_MAX_MATCHES, ge=1, le=20, description="Max matches to collect"),
    collector: RiotDataCollector = Depends(get_collector_service),
) -> Dict[str, Any]:
    """Triggers data collector orchestration to fetch and persist player account and match telemetry."""
    return collector.collect_player_data(
        game_name=game_name,
        tag_line=tag_line,
        region=region,
        max_matches=max_matches,
    )
