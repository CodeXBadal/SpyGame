"""User model."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from bot.utils.time_utils import utcnow


class UserModel(BaseModel):
    user_id: int
    username: Optional[str] = None
    full_name: str = ""
    language_code: Optional[str] = None

    xp: int = 0
    level: int = 1
    coins: int = 0

    games_played: int = 0
    wins: int = 0
    losses: int = 0
    draws: int = 0
    spy_wins: int = 0
    civilian_wins: int = 0
    correct_guesses: int = 0
    correct_votes: int = 0

    seasonal_xp: int = 0
    seasonal_wins: int = 0
    seasonal_coins: int = 0
    seasonal_id: Optional[str] = None

    achievements: List[str] = Field(default_factory=list)
    last_daily_at: Optional[datetime] = None
    daily_streak: int = 0

    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
