"""
SQLAlchemy Player Entity Model.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime
from app.database.session import Base


class PlayerModel(Base):
    """SQLAlchemy model representing stored player profile identity data."""

    __tablename__ = "players"

    puuid = Column(String(128), primary_key=True, index=True, nullable=False)
    game_name = Column(String(64), index=True, nullable=False)
    tag_line = Column(String(32), index=True, nullable=False)
    region = Column(String(16), nullable=False, default="ap")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
