"""Profile endpoints."""
from __future__ import annotations

from fastapi import APIRouter

from ..dependencies import AvatarServiceDependency, StorageDependency
from ..models import ProfileResponse

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("/{identifier}", response_model=ProfileResponse)
async def profile(
    identifier: str,
    storage: StorageDependency,
    avatars: AvatarServiceDependency,
) -> ProfileResponse:
    resolved_user_id, profile_data = storage.get_profile_by_identifier(identifier)
    avatar_url = await avatars.get_avatar_url(
        resolved_user_id, username=profile_data.get("username")
    )
    return ProfileResponse(
        user_id=resolved_user_id,
        username=profile_data.get("username"),
        full_name=profile_data.get("full_name"),
        avatar_url=avatar_url,
    )
