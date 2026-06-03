"""Season repository."""
from __future__ import annotations

from typing import Optional

from bot.database.mongodb import Database
from bot.models.season import SeasonModel
from bot.utils.time_utils import utcnow


class SeasonRepository:
    def __init__(self, database: Database) -> None:
        self._col = database.db.seasons

    async def get_active(self) -> Optional[SeasonModel]:
        doc = await self._col.find_one({"active": True})
        return SeasonModel(**doc) if doc else None

    async def create(self, season: SeasonModel) -> None:
        await self._col.insert_one(season.model_dump())

    async def deactivate_all(self) -> None:
        await self._col.update_many(
            {"active": True},
            {"$set": {"active": False, "ended_at": utcnow()}},
        )
