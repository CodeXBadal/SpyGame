"""Group settings model."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from bot.utils.time_utils import utcnow


class GroupModel(BaseModel):
    group_id: int
    title: Optional[str] = None
    language: str = "en"

    min_players: int = 3
    max_players: int = 12
    lobby_countdown: int = 60
    question_phase_seconds: int = 300
    discussion_phase_seconds: int = 120
    voting_phase_seconds: int = 60

    games_played: int = 0
    recent_locations: List[str] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
