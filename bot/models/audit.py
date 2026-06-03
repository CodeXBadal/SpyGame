"""Audit log model."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from bot.utils.time_utils import utcnow


class AuditLogModel(BaseModel):
    action: str
    actor_id: Optional[int] = None
    group_id: Optional[int] = None
    game_id: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)
