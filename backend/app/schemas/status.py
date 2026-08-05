"""
Platform Status Domain Pydantic Schemas.

Represents Valorant Status-V1 response DTOs.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PlatformStatusDTO(BaseModel):
    """Valorant Platform Data Status model."""
    id: str = Field(..., description="Platform identifier (e.g. AP, NA)")
    name: str = Field(..., description="Platform region display name")
    locales: List[str] = Field(default_factory=list, description="Supported locale strings")
    maintenance_status: str = Field(default="operational", description="General status of server maintenance")
    incidents: List[Dict[str, Any]] = Field(default_factory=list, description="Active incidents or outages")
    raw_data: Dict[str, Any] = Field(default_factory=dict, description="Complete raw platform status payload")
