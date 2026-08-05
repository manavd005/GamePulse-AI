"""
SQLAlchemy Match Entity Model.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, String, BigInteger, JSON, DateTime
from app.database.session import Base


class MatchModel(Base):
    """SQLAlchemy model representing stored match telemetry data."""

    __tablename__ = "matches"

    match_id = Column(String(128), primary_key=True, index=True, nullable=False)
    puuid = Column(String(128), index=True, nullable=True)
    queue_id = Column(String(32), nullable=True)
    game_start_time = Column(BigInteger, nullable=True)
    raw_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
