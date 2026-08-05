"""
Account Domain Pydantic Schemas.

Represents Riot Account-V1 response DTOs.
"""

from pydantic import BaseModel, Field


class AccountDTO(BaseModel):
    """
    Riot Account Data Transfer Object.
    Represents player identity information returned by Riot Account-V1 API.
    """
    puuid: str = Field(..., description="Encrypted Universally Unique Player Identifier")
    gameName: str = Field(..., description="Player in-game Riot ID name")
    tagLine: str = Field(..., description="Player in-game Riot ID tag (e.g. NA1, 1337)")
