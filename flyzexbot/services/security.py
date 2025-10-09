from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque
from typing import Deque, Dict


class RateLimitGuard:
    def __init__(self, interval: float, burst: int) -> None:
        self._interval = interval
        self._burst = burst
        self._entries: Dict[int, Deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def is_allowed(self, key: int) -> bool:
        async with self._lock:
            bucket = self._entries[key]
            now = time.monotonic()
            while bucket and now - bucket[0] > self._interval:
                bucket.popleft()
            if len(bucket) >= self._burst:
                return False
            bucket.append(now)
            return True

