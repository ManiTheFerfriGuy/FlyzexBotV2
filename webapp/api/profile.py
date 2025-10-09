"""Profile endpoints."""
from __future__ import annotations

from fastapi import APIRouter

from ..dependencies import AvatarServiceDependency, StorageDependency
from ..models import ProfileResponse

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("/{user_id}", response_model=ProfileResponse)
async def profile(
    user_id: int,
    storage: StorageDependency,
    avatars: AvatarServiceDependency,
) -> ProfileResponse:
    profile_data = storage.get_any_profile(user_id)
    avatar_url = await avatars.get_avatar_url(user_id)
    return ProfileResponse(
        user_id=user_id,
        username=profile_data.get("username"),
        full_name=profile_data.get("full_name"),
        avatar_url=avatar_url,
    )
