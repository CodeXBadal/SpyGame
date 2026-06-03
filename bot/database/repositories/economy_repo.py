"""Economy / ledger repository."""
from __future__ import annotations

from typing import Optional

from bot.database.mongodb import Database
from bot.models.economy import EconomyModel


class EconomyRepository:
    def __init__(self, database: Database) -> None:
        self._col = database.db.economy

    async def log(
        self,
        user_id: int,
        xp: int = 0,
        coins: int = 0,
        reason: str = "",
        group_id: Optional[int] = None,
        game_id: Optional[str] = None,
    ) -> None:
        if xp == 0 and coins == 0:
            return
        entry = EconomyModel(
            user_id=user_id,
            delta_xp=xp,
            delta_coins=coins,
            reason=reason,
            group_id=group_id,
            game_id=game_id,
        )
        await self._col.insert_one(entry.model_dump())
