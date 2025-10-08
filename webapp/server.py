"""ASGI application exposing FlyzexBot storage insights."""
from __future__ import annotations

import os
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status, Header
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import urllib.request
import json as _json

from cryptography.fernet import Fernet

from flyzexbot.config import Settings
from flyzexbot.services.security import EncryptionManager
from flyzexbot.services.storage import Application, Storage, configure_timezone

BASE_DIR = Path(__file__).resolve().parent
INDEX_PATH = BASE_DIR / "index.html"
CONFIG_PATH = Path("config/settings.yaml")
EXAMPLE_CONFIG_PATH = Path("config/settings.example.yaml")


def _resolve_config_path() -> Path:
    if CONFIG_PATH.exists():
        return CONFIG_PATH
    return EXAMPLE_CONFIG_PATH


def _application_to_dict(application: Application) -> Dict[str, Any]:
    return {
        "user_id": application.user_id,
        "full_name": application.full_name,
        "username": application.username,
        "answer": application.answer,
        "created_at": application.created_at,
        "language_code": application.language_code,
        "responses": [vars(response) for response in getattr(application, "responses", [])],
    }


def _normalize_user_id(value: str) -> int | str:
    try:
        return int(value)
    except (TypeError, ValueError):
        return value


def _compute_cors_origins(settings: Settings | None) -> list[str]:
    """Build a deterministic list of allowed CORS origins."""

    origins: list[str] = []
    if settings is not None:
        webapp_url = settings.webapp.get_url()
        if webapp_url:
            origins.append(webapp_url)
        host = settings.webapp.host or "localhost"
        port = settings.webapp.port
        origins.extend(
            [
                f"http://{host}:{port}",
                f"https://{host}:{port}",
            ]
        )

    # Common fallbacks for local development / testing
    origins.extend(
        [
            "http://localhost",
            "http://127.0.0.1",
            "http://localhost:8080",
            "http://127.0.0.1:8080",
        ]
    )

    return list(dict.fromkeys(origins))


try:
    _initial_settings_for_cors = Settings.load(_resolve_config_path())
except Exception:
    _initial_settings_for_cors = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings.load(_resolve_config_path())
    app.state.cors_origins = _compute_cors_origins(settings)

    # Apply configured timezone for timestamp formatting
    try:
        configure_timezone(getattr(settings, "system").timezone)
    except Exception:
        pass

    ephemeral_secret = False
    try:
        secret_key = settings.get_secret_key()
    except RuntimeError:
        secret_key = Fernet.generate_key()
        ephemeral_secret = True

    encryption = EncryptionManager(secret_key)

    def _disable_persistence_for_ephemeral_secret(active_storage: Storage) -> None:
        """Prevent disk writes when no persistent secret key is configured."""

        async def _noop(self) -> None:  # noqa: D401 - simple asynchronous no-op
            return None

        active_storage.load = _noop.__get__(active_storage, Storage)  # type: ignore[assignment]
        active_storage.save = _noop.__get__(active_storage, Storage)  # type: ignore[assignment]
        active_storage._backup_path = None  # type: ignore[attr-defined]

    storage = Storage(
        settings.storage.path,
        encryption,
        backup_path=settings.storage.backup_path,
    )
    if ephemeral_secret:
        _disable_persistence_for_ephemeral_secret(storage)
    try:
        await storage.load()
    except RuntimeError:
        if not ephemeral_secret:
            raise

    app.state.uses_ephemeral_secret = ephemeral_secret

    app.state.settings = settings
    app.state.storage = storage
    app.state.avatar_cache = {}
    app.state.bot_token = os.getenv(settings.telegram.bot_token_env)

    try:
        yield
    finally:
        if not ephemeral_secret:
            await storage.save()


app = FastAPI(title="FlyzexBot WebApp", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_compute_cors_origins(_initial_settings_for_cors),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


async def require_admin_api_key(x_admin_api_key: str | None = Header(default=None)) -> None:
    env_key = os.getenv("ADMIN_API_KEY")
    if not env_key:
        # Service misconfiguration: no key set, deny access to sensitive endpoints
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Admin API key not configured.")
    if not x_admin_api_key or x_admin_api_key != env_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")



async def get_storage(request: Request) -> Storage:
    return request.app.state.storage  # type: ignore[return-value]


async def get_settings(request: Request) -> Settings:
    return request.app.state.settings  # type: ignore[return-value]


async def _get_avatar_url(user_id: int, bot_token: Optional[str], cache: dict) -> Optional[str]:
    if not bot_token:
        return None
    now = asyncio.get_event_loop().time()
    cached = cache.get(user_id)
    if cached and cached.get("exp", 0) > now:
        return cached.get("url")

    base = f"https://api.telegram.org/bot{bot_token}"
    # Fetch profile photos
    def _get(url: str) -> dict:
        with urllib.request.urlopen(url) as resp:
            return _json.loads(resp.read().decode("utf-8"))

    try:
        data = await asyncio.to_thread(_get, f"{base}/getUserProfilePhotos?user_id={user_id}&limit=1")
        photos = (data.get("result", {}).get("photos") or []) if data.get("ok") else []
        if not photos:
            cache[user_id] = {"url": None, "exp": now + 300}
            return None
        # Pick the largest size in the first set
        sizes = photos[0] or []
        file_id = None
        max_area = -1
        for s in sizes:
            w, h = int(s.get("width", 0)), int(s.get("height", 0))
            area = w * h
            if area > max_area:
                max_area = area
                file_id = s.get("file_id")
        if not file_id:
            cache[user_id] = {"url": None, "exp": now + 300}
            return None
        file_info = await asyncio.to_thread(_get, f"{base}/getFile?file_id={file_id}")
        file_path = file_info.get("result", {}).get("file_path") if file_info.get("ok") else None
        if not file_path:
            cache[user_id] = {"url": None, "exp": now + 300}
            return None
        url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
        cache[user_id] = {"url": url, "exp": now + 600}
        return url
    except Exception:
        cache[user_id] = {"url": None, "exp": now + 300}
        return None


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return INDEX_PATH.read_text(encoding="utf-8")


@app.get("/api/applications/pending", dependencies=[Depends(require_admin_api_key)])
async def pending_applications(storage: Storage = Depends(get_storage)) -> Dict[str, Any]:
    applications = [_application_to_dict(app) for app in storage.get_pending_applications()]
    return {"total": len(applications), "applications": applications}


class AdminPayload(BaseModel):
    user_id: int = Field(..., ge=1, description="Telegram user identifier.")
    username: str | None = Field(
        None,
        max_length=64,
        description="Public username without the @ prefix.",
    )
    full_name: str | None = Field(None, max_length=128, description="Display name of the admin.")


@app.get("/api/admins", dependencies=[Depends(require_admin_api_key)])
async def list_admins(storage: Storage = Depends(get_storage)) -> Dict[str, Any]:
    admins = storage.get_admin_details()
    return {"total": len(admins), "admins": admins}


@app.get("/api/admins/{user_id}", dependencies=[Depends(require_admin_api_key)])
async def get_admin(user_id: int, storage: Storage = Depends(get_storage)) -> Dict[str, Any]:
    admin = storage.get_admin_profile(user_id)
    if not admin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="دسترسی ادمین یافت نشد.")
    return {"admin": admin}


@app.post("/api/admins", dependencies=[Depends(require_admin_api_key)])
async def create_admin(payload: AdminPayload, storage: Storage = Depends(get_storage)) -> Dict[str, Any]:
    existing = storage.is_admin(payload.user_id)
    username = payload.username or None
    full_name = payload.full_name or None
    created = await storage.add_admin(payload.user_id, username=username, full_name=full_name)
    if not created and existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="ادمین از قبل ثبت شده است.")
    if not created:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="امکان افزودن ادمین وجود ندارد.")
    status_text = "updated" if existing else "created"
    return {"status": status_text}


@app.delete("/api/admins/{user_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin_api_key)])
async def delete_admin(user_id: int, storage: Storage = Depends(get_storage)) -> None:
    removed = await storage.remove_admin(user_id)
    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ادمین یافت نشد.")


@app.get("/api/xp")
async def xp_leaderboard(
    chat_id: int = Query(..., description="Target chat identifier for the leaderboard."),
    limit: int | None = Query(None, ge=1, description="Maximum number of users to return."),
    storage: Storage = Depends(get_storage),
    settings: Settings = Depends(get_settings),
) -> Dict[str, Any]:
    effective_limit = limit or settings.xp.leaderboard_size
    leaderboard = [
        {"user_id": _normalize_user_id(user_id), "score": score}
        for user_id, score in storage.get_xp_leaderboard(chat_id, effective_limit)
    ]
    return {"chat_id": chat_id, "limit": effective_limit, "leaderboard": leaderboard}


@app.get("/api/cups")
async def cups(
    chat_id: int = Query(..., description="Target chat identifier for the cup history."),
    limit: int | None = Query(None, ge=1, description="Maximum number of cups to return."),
    storage: Storage = Depends(get_storage),
    settings: Settings = Depends(get_settings),
) -> Dict[str, Any]:
    effective_limit = limit or settings.cups.leaderboard_size
    cups_payload: List[Dict[str, Any]] = storage.get_cups(chat_id, effective_limit)
    return {"chat_id": chat_id, "limit": effective_limit, "cups": cups_payload}


@app.get("/api/leaderboard/xp/top")
async def leaderboard_xp_top(
    limit: int | None = Query(10, ge=1, le=100, description="Number of users to return (default 10)."),
    storage: Storage = Depends(get_storage),
) -> Dict[str, Any]:
    entries: List[Dict[str, Any]] = []
    for rank, (user_id, score) in enumerate(storage.get_global_xp_top(limit or 10), start=1):
        uid = _normalize_user_id(user_id)
        profile = storage.get_any_profile(int(uid)) if isinstance(uid, int) else {"username": None, "full_name": None}
        entries.append(
            {
                "rank": rank,
                "user_id": uid,
                "username": profile.get("username"),
                "full_name": profile.get("full_name"),
                "xp": score,
            }
        )
    return {"total": len(entries), "leaderboard": entries}


@app.get("/api/leaderboard/cups/top")
async def leaderboard_cups_top(
    limit: int | None = Query(10, ge=1, le=100, description="Number of users to return (default 10)."),
    storage: Storage = Depends(get_storage),
) -> Dict[str, Any]:
    entries: List[Dict[str, Any]] = []
    for rank, (user_id, wins) in enumerate(storage.get_cup_wins_top(limit or 10), start=1):
        uid = _normalize_user_id(user_id)
        profile = storage.get_any_profile(int(uid)) if isinstance(uid, int) else {"username": None, "full_name": None}
        entries.append(
            {
                "rank": rank,
                "user_id": uid,
                "username": profile.get("username"),
                "full_name": profile.get("full_name"),
                "cups": wins,
            }
        )
    return {"total": len(entries), "leaderboard": entries}


@app.get("/api/profile/{user_id}")
async def profile(user_id: int, request: Request, storage: Storage = Depends(get_storage)) -> Dict[str, Any]:
    profile = storage.get_any_profile(user_id)
    token = request.app.state.bot_token  # type: ignore[attr-defined]
    cache = request.app.state.avatar_cache  # type: ignore[attr-defined]
    avatar_url = await _get_avatar_url(user_id, token, cache)
    return {
        "user_id": user_id,
        "username": profile.get("username"),
        "full_name": profile.get("full_name"),
        "avatar_url": avatar_url,
    }


@app.get("/api/applications/insights", dependencies=[Depends(require_admin_api_key)])
async def application_insights(storage: Storage = Depends(get_storage)) -> Dict[str, Any]:
    stats_getter = getattr(storage, "get_application_statistics", None)
    if callable(stats_getter):
        return stats_getter()
    return {
        "pending": 0,
        "status_counts": {},
        "languages": {},
        "total": 0,
        "average_pending_answer_length": 0.0,
        "recent_updates": [],
    }


__all__ = ["app"]
