"""Lightweight in-memory cache with TTL support."""
from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, Optional, Tuple


class CacheManager:
    """Thread-safe (asyncio) in-memory cache with expirations."""

    def __init__(self) -> None:
        # key -> (value, expires_at | None)
        self._store: Dict[str, Tuple[Any, Optional[float]]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            item = self._store.get(key)
            if not item:
                return None
            value, expires = item
            if expires is not None and time.time() > expires:
                self._store.pop(key, None)
                return None
            return value

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        async with self._lock:
            expires = time.time() + ttl if ttl else None
            self._store[key] = (value, expires)

    async def delete(self, key: str) -> None:
        async with self._lock:
            self._store.pop(key, None)

    async def exists(self, key: str) -> bool:
        return await self.get(key) is not None

    async def cleanup(self) -> int:
        """Remove expired entries. Returns count removed."""
        async with self._lock:
            now = time.time()
            expired_keys = [
                k for k, (_, exp) in self._store.items() if exp is not None and exp < now
            ]
            for k in expired_keys:
                self._store.pop(k, None)
            return len(expired_keys)

    async def size(self) -> int:
        return len(self._store)


_cache: Optional[CacheManager] = None


def get_cache() -> CacheManager:
    global _cache
    if _cache is None:
        _cache = CacheManager()
    return _cache
