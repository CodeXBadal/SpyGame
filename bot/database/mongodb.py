"""MongoDB async connection manager."""
from __future__ import annotations

import asyncio
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from bot.config import settings
from bot.utils.logger import get_logger

log = get_logger(__name__)


class Database:
    """Wraps a Motor client and exposes the active database."""

    def __init__(self) -> None:
        self._client: Optional[AsyncIOMotorClient] = None
        self._db: Optional[AsyncIOMotorDatabase] = None
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        async with self._lock:
            if self._client is not None:
                return
            log.info("Connecting to MongoDB at %s", settings.mongo_uri)
            self._client = AsyncIOMotorClient(
                settings.mongo_uri,
                maxPoolSize=settings.mongo_max_pool,
                minPoolSize=settings.mongo_min_pool,
                serverSelectionTimeoutMS=10_000,
                retryWrites=True,
            )
            self._db = self._client[settings.mongo_db_name]
            # ping
            await self._client.admin.command("ping")
            log.info("MongoDB connected. Database=%s", settings.mongo_db_name)

    async def disconnect(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None
            self._db = None
            log.info("MongoDB connection closed.")

    async def health_check(self) -> bool:
        try:
            if self._client is None:
                return False
            await self._client.admin.command("ping")
            return True
        except Exception as exc:  # pragma: no cover
            log.error("MongoDB health check failed: %s", exc)
            return False

    @property
    def db(self) -> AsyncIOMotorDatabase:
        if self._db is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._db


_database: Optional[Database] = None


def get_database() -> Database:
    """Singleton accessor."""
    global _database
    if _database is None:
        _database = Database()
    return _database
