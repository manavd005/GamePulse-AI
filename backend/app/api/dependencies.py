"""
FastAPI Dependency Providers Module.

Provides Dependency Injection providers for database sessions, API clients,
repositories, and domain services. Enables seamless mocking during unit tests.
Uses functools.lru_cache for singleton management without global variables.
"""

from functools import lru_cache
from typing import Generator
from fastapi import Depends
from sqlalchemy.orm import Session

from app.clients.riot_client import RiotClient
from app.database.session import get_db_session
from app.repositories.match_repository import IMatchRepository, SQLAlchemyMatchRepository
from app.repositories.player_repository import IPlayerRepository, SQLAlchemyPlayerRepository
from app.services.riot.account_service import AccountService
from app.services.riot.match_service import MatchService
from app.services.riot.status_service import StatusService
from app.services.riot.collector import RiotDataCollector


@lru_cache
def get_riot_client() -> RiotClient:
    """
    Dependency provider for RiotClient instance.
    Uses lru_cache to maintain a clean singleton throughout the application.
    """
    return RiotClient()


def get_player_repository(db: Session = Depends(get_db_session)) -> IPlayerRepository:
    """Dependency provider for Player Repository abstraction."""
    return SQLAlchemyPlayerRepository(db_session=db)


def get_match_repository(db: Session = Depends(get_db_session)) -> IMatchRepository:
    """Dependency provider for Match Repository abstraction."""
    return SQLAlchemyMatchRepository(db_session=db)


def get_account_service(
    client: RiotClient = Depends(get_riot_client),
) -> AccountService:
    """Dependency provider for AccountService."""
    return AccountService(riot_client=client)


def get_match_service(
    client: RiotClient = Depends(get_riot_client),
) -> MatchService:
    """Dependency provider for MatchService."""
    return MatchService(riot_client=client)


def get_status_service(
    client: RiotClient = Depends(get_riot_client),
) -> StatusService:
    """Dependency provider for StatusService."""
    return StatusService(riot_client=client)


def get_collector_service(
    account_service: AccountService = Depends(get_account_service),
    match_service: MatchService = Depends(get_match_service),
    status_service: StatusService = Depends(get_status_service),
    player_repo: IPlayerRepository = Depends(get_player_repository),
    match_repo: IMatchRepository = Depends(get_match_repository),
) -> RiotDataCollector:
    """Dependency provider for RiotDataCollector."""
    return RiotDataCollector(
        account_service=account_service,
        match_service=match_service,
        status_service=status_service,
        player_repo=player_repo,
        match_repo=match_repo,
    )
