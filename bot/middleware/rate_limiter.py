"""In-memory token bucket rate limiter for anti-abuse."""
from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque
from typing import Deque, Dict, Optional

from bot.config import settings


class RateLimiter:
    """Sliding-window rate limiter keyed by user id (+ optional command)."""

    def __init__(self, window: int, max_calls: int) -> None:
        self.window = window
        self.max_calls = max_calls
        self._buckets: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def allow(self, key: str) -> bool:
        async with self._lock:
            now = time.time()
            bucket = self._buckets[key]
            while bucket and bucket[0] <= now - self.window:
                bucket.popleft()
            if len(bucket) >= self.max_calls:
                return False
            bucket.append(now)
            return True

    async def cleanup(self) -> int:
        async with self._lock:
            now = time.time()
            removed = 0
            empty_keys = []
            for k, bucket in self._buckets.items():
                while bucket and bucket[0] <= now - self.window:
                    bucket.popleft()
                    removed += 1
                if not bucket:
                    empty_keys.append(k)
            for k in empty_keys:
                self._buckets.pop(k, None)
            return removed


_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    global _limiter
    if _limiter is None:
        _limiter = RateLimiter(
            window=settings.rate_limit_window,
            max_calls=settings.rate_limit_max,
        )
    return _limiter
