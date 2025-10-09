"""ASGI application exposing FlyzexBot storage insights."""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from cryptography.fernet import Fernet
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from flyzexbot.config import Settings
from flyzexbot.services.security import EncryptionManager
from flyzexbot.services.storage import Storage, configure_timezone

from .api import router as api_router
from .avatar import AvatarService

BASE_DIR = Path(__file__).resolve().parent
INDEX_PATH = BASE_DIR / "index.html"
CONFIG_PATH = Path("config/settings.yaml")
EXAMPLE_CONFIG_PATH = Path("config/settings.example.yaml")


def _resolve_config_path() -> Path:
    if CONFIG_PATH.exists():
        return CONFIG_PATH
    return EXAMPLE_CONFIG_PATH


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

    storage = Storage(
        settings.storage.path,
        encryption,
        backup_path=settings.storage.backup_path,
    )
    if ephemeral_secret:
        storage.disable_persistence()
    try:
        await storage.load()
    except RuntimeError:
        if not ephemeral_secret:
            raise

    bot_token = os.getenv(settings.telegram.bot_token_env)
    avatar_service = AvatarService(bot_token)

    app.state.uses_ephemeral_secret = ephemeral_secret
    app.state.settings = settings
    app.state.storage = storage
    app.state.avatar_service = avatar_service

    try:
        yield
    finally:
        await avatar_service.close()
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
app.include_router(api_router)


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return INDEX_PATH.read_text(encoding="utf-8")


__all__: list[str] = ["app"]
