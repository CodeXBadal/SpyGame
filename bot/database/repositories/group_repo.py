"""Group repository."""
from __future__ import annotations

from typing import List, Optional

from bot.config import settings
from bot.database.mongodb import Database
from bot.models.group import GroupModel
from bot.utils.time_utils import utcnow


class GroupRepository:
    def __init__(self, database: Database) -> None:
        self._col = database.db.groups

    async def get(self, group_id: int) -> Optional[GroupModel]:
        doc = await self._col.find_one({"group_id": group_id})
        return GroupModel(**doc) if doc else None

    async def get_or_create(
        self, group_id: int, title: Optional[str] = None
    ) -> GroupModel:
        existing = await self.get(group_id)
        if existing:
            if title and existing.title != title:
                await self._col.update_one(
                    {"group_id": group_id},
                    {"$set": {"title": title, "updated_at": utcnow()}},
                )
                existing.title = title
            return existing
        group = GroupModel(
            group_id=group_id,
            title=title,
            min_players=settings.default_min_players,
            max_players=settings.default_max_players,
            lobby_countdown=settings.lobby_countdown,
            question_phase_seconds=settings.question_phase_seconds,
            discussion_phase_seconds=settings.discussion_phase_seconds,
            voting_phase_seconds=settings.voting_phase_seconds,
        )
        await self._col.insert_one(group.model_dump())
        return group

    async def update_settings(self, group_id: int, **fields) -> None:
        if not fields:
            return
        fields["updated_at"] = utcnow()
        await self._col.update_one({"group_id": group_id}, {"$set": fields})

    async def push_recent_location(self, group_id: int, location: str, keep: int) -> None:
        await self._col.update_one(
            {"group_id": group_id},
            {
                "$push": {
                    "recent_locations": {
                        "$each": [location],
                        "$slice": -abs(keep),
                    }
                },
                "$inc": {"games_played": 1},
                "$set": {"updated_at": utcnow()},
            },
        )

    async def top_groups(self, limit: int = 10) -> List[GroupModel]:
        cursor = self._col.find().sort("games_played", -1).limit(limit)
        return [GroupModel(**doc) async for doc in cursor]

    async def count(self) -> int:
        return await self._col.count_documents({})
