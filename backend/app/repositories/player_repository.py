"""
Player Repository Module.

Defines the IPlayerRepository interface and concrete SQLAlchemy implementation.
"""

from abc import abstractmethod
from typing import List, Optional
from sqlalchemy.orm import Session

from app.core.constants import DEFAULT_OFFSET, DEFAULT_PAGE_SIZE
from app.models.player import PlayerModel
from app.repositories.base import IBaseRepository


class IPlayerRepository(IBaseRepository[PlayerModel]):
    """Interface for Player database persistence operations."""

    @abstractmethod
    def get_by_riot_id(self, game_name: str, tag_line: str) -> Optional[PlayerModel]:
        """Retrieves a player by game_name and tag_line."""
        pass


class SQLAlchemyPlayerRepository(IPlayerRepository):
    """Concrete SQLAlchemy implementation of IPlayerRepository."""

    def __init__(self, db_session: Session) -> None:
        """
        Initializes repository with a database session.

        Args:
            db_session (Session): Transactional SQLAlchemy session.
        """
        self.db = db_session

    def get_by_id(self, entity_id: str) -> Optional[PlayerModel]:
        """Retrieves a player by PUUID."""
        return self.db.query(PlayerModel).filter(PlayerModel.puuid == entity_id).first()

    def get_by_riot_id(self, game_name: str, tag_line: str) -> Optional[PlayerModel]:
        """Retrieves a player by game name and tag line (case-insensitive)."""
        return (
            self.db.query(PlayerModel)
            .filter(
                PlayerModel.game_name.ilike(game_name),
                PlayerModel.tag_line.ilike(tag_line),
            )
            .first()
        )

    def add(self, entity: PlayerModel) -> PlayerModel:
        """Persists or updates a player record."""
        existing = self.get_by_id(entity.puuid)
        if existing:
            existing.game_name = entity.game_name
            existing.tag_line = entity.tag_line
            existing.region = entity.region
            self.db.commit()
            self.db.refresh(existing)
            return existing

        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def list(self, limit: int = DEFAULT_PAGE_SIZE, offset: int = DEFAULT_OFFSET) -> List[PlayerModel]:
        """Lists player records with pagination."""
        return self.db.query(PlayerModel).offset(offset).limit(limit).all()

    def delete(self, entity_id: str) -> bool:
        """Deletes a player record by PUUID."""
        record = self.get_by_id(entity_id)
        if record:
            self.db.delete(record)
            self.db.commit()
            return True
        return False
