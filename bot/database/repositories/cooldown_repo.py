"""Persistent cooldown repository (TTL-backed)."""
from __future__ import annotations

from datetime import timedelta
from typing import Optional

from bot.database.mongodb import Database
from bot.utils.time_utils import utcnow


class CooldownRepository:
    def __init__(self, database: Database) -> None:
        self._col = database.db.cooldowns

    async def set(self, user_id: int, key: str, seconds: int) -> None:
        expires = utcnow() + timedelta(seconds=int(seconds))
        await self._col.update_one(
            {"user_id": user_id, "key": key},
            {"$set": {"expires_at": expires}},
            upsert=True,
        )

    async def remaining(self, user_id: int, key: str) -> int:
        doc = await self._col.find_one({"user_id": user_id, "key": key})
        if not doc:
            return 0
        expires = doc["expires_at"]
        if expires.tzinfo is None:
            from datetime import timezone
            expires = expires.replace(tzinfo=timezone.utc)
        remaining = int((expires - utcnow()).total_seconds())
        return max(0, remaining)

    async def clear(self, user_id: int, key: str) -> None:
        await self._col.delete_one({"user_id": user_id, "key": key})
