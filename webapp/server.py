"""ASGI application exposing FlyzexBot storage insights."""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from flyzexbot.config import Settings
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


def _normalise_base_path(path: str) -> str:
    """Return a cleaned path prefix suitable for mounting the application."""

    if not path:
        return ""
    trimmed = path.strip()
    if not trimmed or trimmed == "/":
        return ""
    if not trimmed.startswith("/"):
        trimmed = f"/{trimmed}"
    return trimmed.rstrip("/")


def _compute_base_path(settings: Settings | None) -> str:
    """Derive the deployment base path from the configured WebApp URL."""

    if settings is None:
        return ""

    url = settings.webapp.get_url()
    if not url:
        return ""

    parsed = urlparse(url)
    return _normalise_base_path(parsed.path or "")


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

_initial_base_path = _compute_base_path(_initial_settings_for_cors)


class PrefixMiddleware:
    """Allow serving the application under an arbitrary URL prefix."""

    def __init__(self, app: FastAPI) -> None:
        self.app = app
        self._state = getattr(app, "state", None)

    async def __call__(self, scope, receive, send):  # type: ignore[override]
        if scope.get("type") not in {"http", "websocket"}:
            await self.app(scope, receive, send)
            return

        prefix = ""
        if self._state is not None:
            prefix = getattr(self._state, "base_path", "") or ""

        normalised = prefix.rstrip("/")
        if normalised and normalised != "/":
            if not normalised.startswith("/"):
                normalised = f"/{normalised}"
            path = scope.get("path", "")
            if path.startswith(normalised):
                updated_scope = dict(scope)
                updated_scope["path"] = path[len(normalised):] or "/"

                raw_path = updated_scope.get("raw_path")
                if isinstance(raw_path, (bytes, bytearray)):
                    prefix_bytes = normalised.encode("utf-8")
                    if raw_path.startswith(prefix_bytes):
                        updated_scope["raw_path"] = raw_path[len(prefix_bytes):] or b"/"

                root_path = updated_scope.get("root_path", "")
                updated_scope["root_path"] = (f"{root_path}{normalised}").rstrip("/") or "/"

                await self.app(updated_scope, receive, send)
                return

        await self.app(scope, receive, send)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings.load(_resolve_config_path())
    app.state.cors_origins = _compute_cors_origins(settings)
    app.state.base_path = _compute_base_path(settings)
    app.root_path = app.state.base_path or ""

    # Apply configured timezone for timestamp formatting
    try:
        configure_timezone(getattr(settings, "system").timezone)
    except Exception:
        pass

    encryption: EncryptionManager | None = None
    storage_read_only = False
    secret_key_value = os.getenv(settings.telegram.secret_key_env)
    storage_path_suffix = settings.storage.path.suffix.lower()
    requires_secret = storage_path_suffix in {".enc", ".encrypted"}

    if secret_key_value:
        try:
            encryption = EncryptionManager(secret_key_value.encode("utf-8"))
        except Exception:
            encryption = None
            if requires_secret:
                storage_read_only = True
    elif requires_secret:
        storage_read_only = True

    storage = Storage(
        settings.storage.path,
        None,
        backup_path=settings.storage.backup_path,
    )

    if storage_read_only:
        storage.disable_persistence()

    try:
        await storage.load()
    except RuntimeError:
        storage_read_only = True
        storage.disable_persistence()

    bot_token = os.getenv(settings.telegram.bot_token_env)
    avatar_service = AvatarService(bot_token)

    app.state.storage_read_only = False
    app.state.settings = settings
    app.state.storage = storage
    app.state.avatar_service = avatar_service

    try:
        yield
    finally:
        await avatar_service.close()
        if not app.state.storage_read_only:
            await storage.save()


app = FastAPI(title="FlyzexBot WebApp", lifespan=lifespan)
app.state.base_path = _initial_base_path
app.root_path = _initial_base_path or ""
app.add_middleware(PrefixMiddleware)
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
