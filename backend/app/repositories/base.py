"""
Generic Abstract Base Repository Interface.

Defines standard CRUD contracts for database repository abstractions using centralized pagination defaults.
"""

from abc import ABC, abstractmethod
from typing import Generic, List, Optional, TypeVar

from app.core.constants import DEFAULT_OFFSET, DEFAULT_PAGE_SIZE

T = TypeVar("T")


class IBaseRepository(ABC, Generic[T]):
    """Abstract generic repository interface."""

    @abstractmethod
    def get_by_id(self, entity_id: str) -> Optional[T]:
        """Retrieves an entity by its primary key identifier."""
        pass

    @abstractmethod
    def add(self, entity: T) -> T:
        """Persists a new entity to storage."""
        pass

    @abstractmethod
    def list(self, limit: int = DEFAULT_PAGE_SIZE, offset: int = DEFAULT_OFFSET) -> List[T]:
        """Lists entities with pagination."""
        pass

    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        """Deletes an entity by primary key identifier."""
        pass
