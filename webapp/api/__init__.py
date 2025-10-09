"""API routers for the FlyzexBot web application."""
from __future__ import annotations

from fastapi import APIRouter

from . import admins, applications, health, leaderboard, profile


router = APIRouter()
router.include_router(applications.router)
router.include_router(admins.router)
router.include_router(leaderboard.router)
router.include_router(profile.router)
router.include_router(health.router)

__all__ = ["router"]
