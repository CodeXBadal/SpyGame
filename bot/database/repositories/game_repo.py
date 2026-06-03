"""Game repository."""
from __future__ import annotations

from typing import List, Optional

from bot.database.mongodb import Database
from bot.models.game import GameModel, GameStatus
from bot.utils.time_utils import utcnow


class GameRepository:
    def __init__(self, database: Database) -> None:
        self._col = database.db.games

    async def save(self, game: GameModel) -> None:
        data = game.model_dump()
        await self._col.update_one(
            {"game_id": game.game_id}, {"$set": data}, upsert=True
        )

    async def get(self, game_id: str) -> Optional[GameModel]:
        doc = await self._col.find_one({"game_id": game_id})
        return GameModel(**doc) if doc else None

    async def get_active_for_group(self, group_id: int) -> Optional[GameModel]:
        doc = await self._col.find_one(
            {
                "group_id": group_id,
                "status": {"$in": [GameStatus.LOBBY.value, GameStatus.RUNNING.value]},
            }
        )
        return GameModel(**doc) if doc else None

    async def list_active(self) -> List[GameModel]:
        cursor = self._col.find(
            {"status": {"$in": [GameStatus.LOBBY.value, GameStatus.RUNNING.value]}}
        )
        return [GameModel(**doc) async for doc in cursor]

    async def end_game(self, game_id: str, winner: Optional[str]) -> None:
        await self._col.update_one(
            {"game_id": game_id},
            {
                "$set": {
                    "status": GameStatus.ENDED.value,
                    "winner": winner,
                    "ended_at": utcnow(),
                }
            },
        )

    async def cancel_game(self, game_id: str) -> None:
        await self._col.update_one(
            {"game_id": game_id},
            {
                "$set": {
                    "status": GameStatus.CANCELLED.value,
                    "ended_at": utcnow(),
                }
            },
        )

    async def count_total(self) -> int:
        return await self._col.count_documents({})

    async def count_active(self) -> int:
        return await self._col.count_documents(
            {"status": {"$in": [GameStatus.LOBBY.value, GameStatus.RUNNING.value]}}
        )
