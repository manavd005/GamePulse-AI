"""
API v1 Router Router Module.

Combines all v1 endpoint sub-routers into a unified router hierarchy.
"""

from fastapi import APIRouter
from app.api.routers.health import router as health_router
from app.api.routers.players import router as players_router
from app.api.routers.matches import router as matches_router

api_v1_router = APIRouter(prefix="/v1")
api_v1_router.include_router(health_router)
api_v1_router.include_router(players_router)
api_v1_router.include_router(matches_router)
