"""Utilities for retrieving and caching Telegram user avatars."""
from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, Optional

import httpx


class AvatarService:
    """Lightweight helper for retrieving Telegram profile images."""

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
        self._cache: Dict[int, Dict[str, Any]] = {}

    async def close(self) -> None:
        await self._client.aclose()

    async def get_avatar_url(self, user_id: int) -> Optional[str]:
        if not self._bot_token:
            return None

        found, cached_value = await self._get_cached(user_id)
        if found:
            return cached_value

        url = await self._fetch_avatar_url(user_id)
        await self._store_cache(user_id, url)
        return url

    async def _get_cached(self, user_id: int) -> tuple[bool, Optional[str]]:
        async with self._lock:
            entry = self._cache.get(user_id)
            if not entry:
                return False, None
            if entry["exp"] < time.monotonic():
                self._cache.pop(user_id, None)
                return False, None
            return True, entry["url"]

    async def _store_cache(self, user_id: int, url: Optional[str]) -> None:
        ttl = self._empty_ttl if url is None else self._cache_ttl
        async with self._lock:
            self._cache[user_id] = {"url": url, "exp": time.monotonic() + ttl}

    async def _fetch_avatar_url(self, user_id: int) -> Optional[str]:
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
