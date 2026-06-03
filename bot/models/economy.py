"""Economy ledger model."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from bot.utils.time_utils import utcnow


class EconomyModel(BaseModel):
    user_id: int
    delta_xp: int = 0
    delta_coins: int = 0
    reason: str = ""
    group_id: Optional[int] = None
    game_id: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)
