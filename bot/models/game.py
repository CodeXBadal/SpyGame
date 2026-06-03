"""Game-related domain models."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from bot.utils.time_utils import utcnow


class Role(str, Enum):
    SPY = "spy"
    CIVILIAN = "civilian"


class GameStatus(str, Enum):
    LOBBY = "lobby"
    RUNNING = "running"
    ENDED = "ended"
    CANCELLED = "cancelled"


class GamePhase(str, Enum):
    LOBBY = "lobby"
    ROLE_REVEAL = "role_reveal"
    QUESTION = "question"
    DISCUSSION = "discussion"
    VOTING = "voting"
    RESULT = "result"


class PlayerModel(BaseModel):
    user_id: int
    username: Optional[str] = None
    full_name: str = ""
    role: Optional[Role] = None
    is_alive: bool = True
    joined_at: datetime = Field(default_factory=utcnow)
    dm_ok: bool = True  # whether DM delivery succeeded


class VoteModel(BaseModel):
    voter_id: int
    target_id: int
    created_at: datetime = Field(default_factory=utcnow)


class GameModel(BaseModel):
    """Single game state, one per group at a time."""

    game_id: str
    group_id: int
    host_id: int
    status: GameStatus = GameStatus.LOBBY
    phase: GamePhase = GamePhase.LOBBY

    players: Dict[str, PlayerModel] = Field(default_factory=dict)
    votes: Dict[str, VoteModel] = Field(default_factory=dict)

    location: Optional[str] = None
    spy_id: Optional[int] = None
    winner: Optional[str] = None  # "spy" | "civilians" | "draw"

    min_players: int = 3
    max_players: int = 12

    current_asker_id: Optional[int] = None
    question_count: int = 0
    question_history: List[Dict] = Field(default_factory=list)

    lobby_message_id: Optional[int] = None
    chat_message_id: Optional[int] = None

    created_at: datetime = Field(default_factory=utcnow)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    phase_deadline: Optional[datetime] = None

    @property
    def player_count(self) -> int:
        return len(self.players)

    @property
    def alive_player_ids(self) -> List[int]:
        return [p.user_id for p in self.players.values() if p.is_alive]

    def has_player(self, user_id: int) -> bool:
        return str(user_id) in self.players

    def get_player(self, user_id: int) -> Optional[PlayerModel]:
        return self.players.get(str(user_id))
