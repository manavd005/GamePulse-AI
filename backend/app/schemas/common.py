"""
Common Schemas & Data Transfer Objects (DTOs).

Defines standard response models for health checks, connection tests, and API errors.
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ConnectionResult(BaseModel):
    """Result model for connection verification checks."""
    success: bool = Field(..., description="Indicates if the connection attempt succeeded")
    message: str = Field(..., description="Human-readable status summary")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Optional payload returned from remote service")
    error_code: Optional[int] = Field(default=None, description="HTTP or application error status code if failed")


class HealthCheckResult(BaseModel):
    """Health check status model for system status services."""
    status: str = Field(..., description="Overall health state (healthy, degraded, down)")
    region: str = Field(..., description="Target platform region checked")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Detailed status breakdown")


class ApiError(BaseModel):
    """Standardized API Error payload model."""
    status_code: int = Field(..., description="HTTP status code")
    message: str = Field(..., description="Error summary message")
    details: Optional[str] = Field(default=None, description="Contextual error details or response body snippet")
