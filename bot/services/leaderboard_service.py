"""Leaderboard queries."""
from __future__ import annotations

from typing import List

from bot.database.repositories import UserRepository
from bot.models.user import UserModel


class LeaderboardService:
    def __init__(self, users: UserRepository) -> None:
        self._users = users

    async def top_xp(self, limit: int = 10) -> List[UserModel]:
        return await self._users.top_by("xp", limit)

    async def top_wins(self, limit: int = 10) -> List[UserModel]:
        return await self._users.top_by("wins", limit)

    async def top_coins(self, limit: int = 10) -> List[UserModel]:
        return await self._users.top_by("coins", limit)

    async def top_seasonal_xp(self, limit: int = 10) -> List[UserModel]:
        return await self._users.top_by("seasonal_xp", limit)

    async def top_seasonal_wins(self, limit: int = 10) -> List[UserModel]:
        return await self._users.top_by("seasonal_wins", limit)

    async def rank_of(self, user_id: int, field: str = "xp") -> int:
        return await self._users.rank_of(user_id, field=field)
