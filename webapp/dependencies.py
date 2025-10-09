"""Shared FastAPI dependencies for the FlyzexBot web application."""
from __future__ import annotations

import os
from typing import Annotated, Optional

from fastapi import Depends, Header, HTTPException, Request, status

from flyzexbot.config import Settings
from flyzexbot.services.storage import Storage

from .avatar import AvatarService

AdminAPIKeyHeader = Annotated[Optional[str], Header(alias="X-Admin-Api-Key")]


async def require_admin_api_key(x_admin_api_key: AdminAPIKeyHeader = None) -> None:
    """Ensure that the request carries a valid admin API key."""

    env_key = os.getenv("ADMIN_API_KEY")
    if not env_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin API key not configured.",
        )
    if not x_admin_api_key or x_admin_api_key != env_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")


def get_storage(request: Request) -> Storage:
    storage = getattr(request.app.state, "storage", None)
    if storage is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Storage not initialised.")
    return storage  # type: ignore[return-value]


def get_settings(request: Request) -> Settings:
    settings = getattr(request.app.state, "settings", None)
    if settings is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Settings not loaded.")
    return settings  # type: ignore[return-value]


def get_avatar_service(request: Request) -> AvatarService:
    service = getattr(request.app.state, "avatar_service", None)
    if service is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Avatar service unavailable.")
    return service  # type: ignore[return-value]


StorageDependency = Annotated[Storage, Depends(get_storage)]
SettingsDependency = Annotated[Settings, Depends(get_settings)]
AvatarServiceDependency = Annotated[AvatarService, Depends(get_avatar_service)]
