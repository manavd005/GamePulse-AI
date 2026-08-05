"""
Match Repository Module.

Defines the IMatchRepository interface and concrete SQLAlchemy implementation.
"""

from abc import abstractmethod
from typing import List, Optional
from sqlalchemy.orm import Session

from app.core.constants import DEFAULT_MATCH_LIMIT, DEFAULT_OFFSET, DEFAULT_PAGE_SIZE
from app.models.match import MatchModel
from app.repositories.base import IBaseRepository


class IMatchRepository(IBaseRepository[MatchModel]):
    """Interface for Match database persistence operations."""

    @abstractmethod
    def list_by_puuid(self, puuid: str, limit: int = DEFAULT_MATCH_LIMIT) -> List[MatchModel]:
        """Lists matches associated with a player PUUID."""
        pass


class SQLAlchemyMatchRepository(IMatchRepository):
    """Concrete SQLAlchemy implementation of IMatchRepository."""

    def __init__(self, db_session: Session) -> None:
        """
        Initializes repository with a database session.

        Args:
            db_session (Session): Transactional SQLAlchemy session.
        """
        self.db = db_session

    def get_by_id(self, entity_id: str) -> Optional[MatchModel]:
        """Retrieves a match by match_id."""
        return self.db.query(MatchModel).filter(MatchModel.match_id == entity_id).first()

    def list_by_puuid(self, puuid: str, limit: int = DEFAULT_MATCH_LIMIT) -> List[MatchModel]:
        """Lists recent matches for a player PUUID."""
        return (
            self.db.query(MatchModel)
            .filter(MatchModel.puuid == puuid)
            .order_by(MatchModel.game_start_time.desc())
            .limit(limit)
            .all()
        )

    def add(self, entity: MatchModel) -> MatchModel:
        """Persists or updates a match record."""
        existing = self.get_by_id(entity.match_id)
        if existing:
            existing.puuid = entity.puuid or existing.puuid
            existing.raw_json = entity.raw_json or existing.raw_json
            self.db.commit()
            self.db.refresh(existing)
            return existing

        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def list(self, limit: int = DEFAULT_PAGE_SIZE, offset: int = DEFAULT_OFFSET) -> List[MatchModel]:
        """Lists match records with pagination."""
        return self.db.query(MatchModel).offset(offset).limit(limit).all()

    def delete(self, entity_id: str) -> bool:
        """Deletes a match record by match_id."""
        record = self.get_by_id(entity_id)
        if record:
            self.db.delete(record)
            self.db.commit()
            return True
        return False
