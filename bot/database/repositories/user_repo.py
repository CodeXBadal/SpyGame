"""User repository."""
from __future__ import annotations

from typing import List, Optional

from bot.database.mongodb import Database
from bot.models.user import UserModel
from bot.utils.time_utils import utcnow


class UserRepository:
    """CRUD for users collection."""

    def __init__(self, database: Database) -> None:
        self._db = database
        self._col = database.db.users

    async def get(self, user_id: int) -> Optional[UserModel]:
        doc = await self._col.find_one({"user_id": user_id})
        return UserModel(**doc) if doc else None

    async def get_or_create(
        self,
        user_id: int,
        username: Optional[str] = None,
        full_name: str = "",
        language_code: Optional[str] = None,
    ) -> UserModel:
        existing = await self.get(user_id)
        if existing:
            # Lightweight touch-up of changing fields
            updates = {}
            if username and username != existing.username:
                updates["username"] = username
            if full_name and full_name != existing.full_name:
                updates["full_name"] = full_name
            if language_code and language_code != existing.language_code:
                updates["language_code"] = language_code
            if updates:
                updates["updated_at"] = utcnow()
                await self._col.update_one({"user_id": user_id}, {"$set": updates})
                for k, v in updates.items():
                    setattr(existing, k, v)
            return existing
        user = UserModel(
            user_id=user_id,
            username=username,
            full_name=full_name,
            language_code=language_code,
        )
        await self._col.insert_one(user.model_dump())
        return user

    async def add_xp_coins(
        self, user_id: int, xp: int = 0, coins: int = 0
    ) -> None:
        if xp == 0 and coins == 0:
            return
        await self._col.update_one(
            {"user_id": user_id},
            {
                "$inc": {
                    "xp": xp,
                    "coins": coins,
                    "seasonal_xp": xp,
                    "seasonal_coins": coins,
                },
                "$set": {"updated_at": utcnow()},
            },
        )

    async def increment_counters(self, user_id: int, **fields: int) -> None:
        if not fields:
            return
        await self._col.update_one(
            {"user_id": user_id},
            {"$inc": fields, "$set": {"updated_at": utcnow()}},
        )

    async def set_level(self, user_id: int, level: int) -> None:
        await self._col.update_one(
            {"user_id": user_id},
            {"$set": {"level": level, "updated_at": utcnow()}},
        )

    async def add_achievement(self, user_id: int, code: str) -> bool:
        result = await self._col.update_one(
            {"user_id": user_id, "achievements": {"$ne": code}},
            {"$push": {"achievements": code}, "$set": {"updated_at": utcnow()}},
        )
        return result.modified_count > 0

    async def set_daily(
        self, user_id: int, last_daily_at, streak: int
    ) -> None:
        await self._col.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "last_daily_at": last_daily_at,
                    "daily_streak": streak,
                    "updated_at": utcnow(),
                }
            },
        )

    async def reset_seasonal(self, season_id: str) -> int:
        result = await self._col.update_many(
            {},
            {
                "$set": {
                    "seasonal_xp": 0,
                    "seasonal_wins": 0,
                    "seasonal_coins": 0,
                    "seasonal_id": season_id,
                    "updated_at": utcnow(),
                }
            },
        )
        return result.modified_count

    async def top_by(
        self, field: str, limit: int = 10
    ) -> List[UserModel]:
        cursor = self._col.find().sort(field, -1).limit(limit)
        return [UserModel(**doc) async for doc in cursor]

    async def rank_of(self, user_id: int, field: str = "xp") -> int:
        user = await self.get(user_id)
        if not user:
            return 0
        value = getattr(user, field, 0)
        higher = await self._col.count_documents({field: {"$gt": value}})
        return higher + 1

    async def count(self) -> int:
        return await self._col.count_documents({})
