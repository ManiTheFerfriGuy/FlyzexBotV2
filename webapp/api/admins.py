"""Administrative endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ..dependencies import StorageDependency, require_admin_api_key
from ..models import AdminDetailResponse, AdminListResponse, AdminModel, AdminMutationResponse

router = APIRouter(prefix="/api/admins", tags=["admins"], dependencies=[Depends(require_admin_api_key)])


class AdminPayload(BaseModel):
    user_id: int = Field(..., ge=1, description="Telegram user identifier.")
    username: str | None = Field(
        None,
        max_length=64,
        description="Public username without the @ prefix.",
    )
    full_name: str | None = Field(
        None,
        max_length=128,
        description="Display name of the admin.",
    )


@router.get("", response_model=AdminListResponse)
async def list_admins(storage: StorageDependency) -> AdminListResponse:
    admins = [AdminModel(**admin) for admin in storage.get_admin_details()]
    return AdminListResponse(total=len(admins), admins=admins)


@router.get("/{user_id}", response_model=AdminDetailResponse)
async def get_admin(user_id: int, storage: StorageDependency) -> AdminDetailResponse:
    admin = storage.get_admin_profile(user_id)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="دسترسی ادمین یافت نشد.",
        )
    return AdminDetailResponse(admin=AdminModel(**admin))


@router.post("", response_model=AdminMutationResponse)
async def create_admin(payload: AdminPayload, storage: StorageDependency) -> AdminMutationResponse:
    existing = storage.is_admin(payload.user_id)
    username = payload.username or None
    full_name = payload.full_name or None
    created = await storage.add_admin(payload.user_id, username=username, full_name=full_name)
    if not created and existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="ادمین از قبل ثبت شده است.",
        )
    if not created:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="امکان افزودن ادمین وجود ندارد.",
        )
    status_text = "updated" if existing else "created"
    return AdminMutationResponse(status=status_text)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_admin(user_id: int, storage: StorageDependency) -> None:
    removed = await storage.remove_admin(user_id)
    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ادمین یافت نشد.")
