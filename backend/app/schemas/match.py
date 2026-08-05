"""
Match Domain Pydantic Schemas.

Represents Valorant Match-V1 response DTOs.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MatchEntryDTO(BaseModel):
    """Brief match reference item in player match history."""
    matchId: str = Field(..., description="Unique match identifier")
    gameStartTimeMillis: int = Field(default=0, description="Epoch timestamp of match start")
    queueId: Optional[str] = Field(default=None, description="Match queue type (e.g. competitive, unrated)")


class MatchlistDTO(BaseModel):
    """Match history list model for a player PUUID."""
    puuid: str = Field(..., description="Encrypted PUUID of player")
    history: List[MatchEntryDTO] = Field(default_factory=list, description="List of recent matches")


class MatchDetailsDTO(BaseModel):
    """Detailed match breakdown model."""
    matchId: str = Field(..., description="Unique match identifier")
    matchInfo: Dict[str, Any] = Field(default_factory=dict, description="Metadata such as map, duration, mode")
    players: List[Dict[str, Any]] = Field(default_factory=list, description="List of participant stats")
    teams: List[Dict[str, Any]] = Field(default_factory=list, description="Team scores and round stats")
    raw_data: Dict[str, Any] = Field(default_factory=dict, description="Complete raw JSON payload from Riot API")
