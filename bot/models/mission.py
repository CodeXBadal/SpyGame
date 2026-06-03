"""Mission model."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, Field

from bot.utils.time_utils import utcnow


class MissionModel(BaseModel):
    mission_id: str
    name: str
    description: str
    period: str  # "daily" | "weekly"
    metric: str  # e.g., "games_played", "wins", "correct_votes"
    target: int = 1
    reward_xp: int = 0
    reward_coins: int = 0


class MissionProgress(BaseModel):
    user_id: int
    mission_id: str
    period_key: str  # e.g. 2026-06-03 or 2026-W22
    progress: int = 0
    target: int = 1
    completed: bool = False
    claimed: bool = False
    updated_at: datetime = Field(default_factory=utcnow)
