"""Utilities for retrieving and caching Telegram user avatars."""
from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, Optional

from urllib.parse import quote

import httpx


class AvatarService:
    """Lightweight helper for retrieving Telegram profile images or fallbacks."""

    _PLACEHOLDER_URL = (
        "https://api.dicebear.com/7.x/thumbs/svg"
        "?backgroundType=gradientLinear"
        "&shapeColor=4865ff,22d1ee"
    )

    def __init__(
        self,
        bot_token: Optional[str],
        *,
        cache_ttl: int = 600,
        empty_ttl: int = 300,
        timeout: float = 10.0,
    ) -> None:
        self._bot_token = bot_token
        self._cache_ttl = cache_ttl
        self._empty_ttl = empty_ttl
        self._client = httpx.AsyncClient(timeout=timeout)
        self._lock = asyncio.Lock()
        self._cache: Dict[str, Dict[str, Any]] = {}

    async def close(self) -> None:
        await self._client.aclose()

    async def get_avatar_url(
        self,
        user_id: Optional[int] = None,
        *,
        username: Optional[str] = None,
    ) -> Optional[str]:
        """Return the best avatar URL for the provided identifiers."""

        normalized_username = self._normalise_username(username)
        cache_key = self._build_cache_key(user_id, normalized_username)
        if cache_key is None:
            return None

        found, cached_value = await self._get_cached(cache_key)
        if found:
            return cached_value

        url = await self._fetch_avatar_url(
            user_id=user_id,
            username=normalized_username,
        )
        await self._store_cache(cache_key, url)
        return url

    async def _get_cached(self, cache_key: str) -> tuple[bool, Optional[str]]:
        async with self._lock:
            entry = self._cache.get(cache_key)
            if not entry:
                return False, None
            if entry["exp"] < time.monotonic():
                self._cache.pop(cache_key, None)
                return False, None
            return True, entry["url"]

    async def _store_cache(self, cache_key: str, url: Optional[str]) -> None:
        ttl = self._empty_ttl if url is None else self._cache_ttl
        async with self._lock:
            self._cache[cache_key] = {"url": url, "exp": time.monotonic() + ttl}

    def _build_cache_key(
        self, user_id: Optional[int], username: Optional[str]
    ) -> Optional[str]:
        if user_id is not None:
            return f"id:{user_id}"
        if username:
            return f"username:{username.casefold()}"
        return None

    async def _fetch_avatar_url(
        self, *, user_id: Optional[int], username: Optional[str]
    ) -> Optional[str]:
        if self._bot_token and user_id is not None:
            telegram_url = await self._fetch_telegram_avatar(user_id)
            if telegram_url:
                return telegram_url

        seed = self._build_seed(user_id=user_id, username=username)
        if not seed:
            return None
        return self._build_placeholder_url(seed)

    async def _fetch_telegram_avatar(self, user_id: int) -> Optional[str]:
        base = f"https://api.telegram.org/bot{self._bot_token}"

        photos = await self._telegram_request(
            f"{base}/getUserProfilePhotos",
            params={"user_id": user_id, "limit": 1},
        )
        if not photos.get("ok"):
            return None
        results = photos.get("result", {})
        photo_sets = results.get("photos") or []
        if not photo_sets:
            return None
        sizes = photo_sets[0] or []
        if not sizes:
            return None

        best = max(
            (size for size in sizes if size.get("file_id")),
            key=lambda item: int(item.get("width", 0)) * int(item.get("height", 0)),
            default=None,
        )
        if not best:
            return None

        file_info = await self._telegram_request(
            f"{base}/getFile", params={"file_id": best.get("file_id")}
        )
        if not file_info.get("ok"):
            return None
        file_path = file_info.get("result", {}).get("file_path")
        if not file_path:
            return None
        return f"https://api.telegram.org/file/bot{self._bot_token}/{file_path}"

    def _build_seed(
        self, *, user_id: Optional[int], username: Optional[str]
    ) -> Optional[str]:
        if username:
            return username.casefold()
        if user_id is not None:
            return str(user_id)
        return None

    def _build_placeholder_url(self, seed: str) -> str:
        encoded_seed = quote(seed, safe="")
        return f"{self._PLACEHOLDER_URL}&seed={encoded_seed}"

    def _normalise_username(self, username: Optional[str]) -> Optional[str]:
        if not isinstance(username, str):
            return None
        trimmed = username.strip()
        if not trimmed:
            return None
        trimmed = trimmed.lstrip("@").strip()
        if not trimmed:
            return None
        return trimmed

    async def _telegram_request(self, url: str, *, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            response = await self._client.get(url, params=params)
        except httpx.HTTPError:
            return {}
        if response.status_code != 200:
            return {}
        try:
            return response.json()
        except ValueError:
            return {}
