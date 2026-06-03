"""Audit log repository."""
from __future__ import annotations

from typing import Any, Dict, Optional

from bot.database.mongodb import Database
from bot.models.audit import AuditLogModel


class AuditRepository:
    def __init__(self, database: Database) -> None:
        self._col = database.db.audit_logs

    async def log(
        self,
        action: str,
        actor_id: Optional[int] = None,
        group_id: Optional[int] = None,
        game_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        entry = AuditLogModel(
            action=action,
            actor_id=actor_id,
            group_id=group_id,
            game_id=game_id,
            payload=payload or {},
        )
        await self._col.insert_one(entry.model_dump())
