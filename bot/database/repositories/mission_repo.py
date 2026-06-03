"""Mission repository."""
from __future__ import annotations

from typing import List, Optional

from bot.database.mongodb import Database
from bot.models.mission import MissionModel, MissionProgress
from bot.utils.time_utils import utcnow


class MissionRepository:
    def __init__(self, database: Database) -> None:
        self._missions = database.db.missions
        self._progress = database.db.mission_progress

    async def upsert_mission(self, mission: MissionModel) -> None:
        await self._missions.update_one(
            {"mission_id": mission.mission_id},
            {"$set": mission.model_dump()},
            upsert=True,
        )

    async def list_missions(self, period: Optional[str] = None) -> List[MissionModel]:
        query = {"period": period} if period else {}
        cursor = self._missions.find(query)
        return [MissionModel(**doc) async for doc in cursor]

    async def get_progress(
        self, user_id: int, mission_id: str, period_key: str
    ) -> Optional[MissionProgress]:
        doc = await self._progress.find_one(
            {"user_id": user_id, "mission_id": mission_id, "period_key": period_key}
        )
        return MissionProgress(**doc) if doc else None

    async def list_progress(
        self, user_id: int, period_key: str
    ) -> List[MissionProgress]:
        cursor = self._progress.find(
            {"user_id": user_id, "period_key": period_key}
        )
        return [MissionProgress(**doc) async for doc in cursor]

    async def increment_progress(
        self,
        user_id: int,
        mission: MissionModel,
        period_key: str,
        amount: int = 1,
    ) -> MissionProgress:
        await self._progress.update_one(
            {
                "user_id": user_id,
                "mission_id": mission.mission_id,
                "period_key": period_key,
            },
            {
                "$inc": {"progress": amount},
                "$setOnInsert": {
                    "target": mission.target,
                    "completed": False,
                    "claimed": False,
                },
                "$set": {"updated_at": utcnow()},
            },
            upsert=True,
        )
        doc = await self._progress.find_one(
            {
                "user_id": user_id,
                "mission_id": mission.mission_id,
                "period_key": period_key,
            }
        )
        progress = MissionProgress(**doc)
        if progress.progress >= progress.target and not progress.completed:
            await self._progress.update_one(
                {
                    "user_id": user_id,
                    "mission_id": mission.mission_id,
                    "period_key": period_key,
                },
                {"$set": {"completed": True, "updated_at": utcnow()}},
            )
            progress.completed = True
        return progress

    async def mark_claimed(
        self, user_id: int, mission_id: str, period_key: str
    ) -> bool:
        result = await self._progress.update_one(
            {
                "user_id": user_id,
                "mission_id": mission_id,
                "period_key": period_key,
                "completed": True,
                "claimed": False,
            },
            {"$set": {"claimed": True, "updated_at": utcnow()}},
        )
        return result.modified_count > 0
