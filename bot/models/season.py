"""Season model."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from bot.utils.time_utils import utcnow


class SeasonModel(BaseModel):
    season_id: str
    name: str
    started_at: datetime = Field(default_factory=utcnow)
    ended_at: Optional[datetime] = None
    active: bool = True
