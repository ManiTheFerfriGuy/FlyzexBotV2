"""Leaderboard endpoints."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from flyzexbot.services.xp import calculate_level_progress

from ..dependencies import SettingsDependency, StorageDependency
from ..models import (
    CupsHistoryResponse,
    CupsLeaderboardResponse,
    CupsEntryModel,
    SimpleLeaderboardResponse,
    XPEntryModel,
    XPLeaderboardResponse,
)

ChatIdParam = Annotated[int, Query(description="Target chat identifier for the leaderboard.")]
LimitParam = Annotated[int | None, Query(ge=1, description="Maximum number of users to return.")]
TopLimitParam = Annotated[int | None, Query(ge=1, le=100, description="Number of users to return (default 10).")]

router = APIRouter(tags=["leaderboard"])


def _normalize_user_id(value: object) -> int | str:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return str(value)


@router.get("/api/xp", response_model=SimpleLeaderboardResponse)
async def xp_leaderboard(
    storage: StorageDependency,
    settings: SettingsDependency,
    chat_id: ChatIdParam,
    limit: LimitParam = None,
) -> SimpleLeaderboardResponse:
    effective_limit = limit or settings.xp.leaderboard_size
    leaderboard = []
    for user_id, score in storage.get_xp_leaderboard(chat_id, effective_limit):
        progress = calculate_level_progress(score)
        leaderboard.append(
            {
                "user_id": _normalize_user_id(user_id),
                "score": score,
                "level": progress.level,
            }
        )
    return SimpleLeaderboardResponse(chat_id=chat_id, limit=effective_limit, leaderboard=leaderboard)


@router.get("/api/cups", response_model=CupsHistoryResponse)
async def cups(
    storage: StorageDependency,
    settings: SettingsDependency,
    chat_id: ChatIdParam,
    limit: LimitParam = None,
) -> CupsHistoryResponse:
    effective_limit = limit or settings.cups.leaderboard_size
    cups_payload = storage.get_cups(chat_id, effective_limit)
    return CupsHistoryResponse(chat_id=chat_id, limit=effective_limit, cups=cups_payload)


@router.get("/api/leaderboard/xp/top", response_model=XPLeaderboardResponse)
async def leaderboard_xp_top(
    storage: StorageDependency,
    limit: TopLimitParam = 10,
) -> XPLeaderboardResponse:
    entries: list[XPEntryModel] = []
    for rank, (user_id, score) in enumerate(storage.get_global_xp_top(limit or 10), start=1):
        uid = _normalize_user_id(user_id)
        profile = storage.get_any_profile(int(uid)) if isinstance(uid, int) else {"username": None, "full_name": None}
        progress = calculate_level_progress(score)
        entries.append(
            XPEntryModel(
                rank=rank,
                user_id=uid,
                username=profile.get("username"),
                full_name=profile.get("full_name"),
                xp=score,
                level=progress.level,
            )
        )
    return XPLeaderboardResponse(total=len(entries), leaderboard=entries)


@router.get("/api/leaderboard/cups/top", response_model=CupsLeaderboardResponse)
async def leaderboard_cups_top(
    storage: StorageDependency,
    limit: TopLimitParam = 10,
) -> CupsLeaderboardResponse:
    entries: list[CupsEntryModel] = []
    for rank, (user_id, wins) in enumerate(storage.get_cup_wins_top(limit or 10), start=1):
        uid = _normalize_user_id(user_id)
        profile = storage.get_any_profile(int(uid)) if isinstance(uid, int) else {"username": None, "full_name": None}
        entries.append(
            CupsEntryModel(
                rank=rank,
                user_id=uid,
                username=profile.get("username"),
                full_name=profile.get("full_name"),
                cups=wins,
            )
        )
    return CupsLeaderboardResponse(total=len(entries), leaderboard=entries)
