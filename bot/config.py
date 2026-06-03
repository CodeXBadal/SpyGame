"""Application configuration loaded from environment variables."""
from __future__ import annotations

import os
from functools import lru_cache
from typing import List

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()


def _get_int(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, str(default)))
    except (TypeError, ValueError):
        return default


def _get_bool(key: str, default: bool) -> bool:
    val = os.getenv(key)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


def _get_id_list(key: str) -> List[int]:
    raw = os.getenv(key, "")
    if not raw:
        return []
    result: List[int] = []
    for part in raw.replace(";", ",").split(","):
        part = part.strip()
        if not part:
            continue
        try:
            result.append(int(part))
        except ValueError:
            continue
    return result


class Settings(BaseModel):
    """Settings model holding all configuration values."""

    # Telegram
    bot_token: str = Field(default_factory=lambda: os.getenv("BOT_TOKEN", ""))
    bot_username: str = Field(default_factory=lambda: os.getenv("BOT_USERNAME", "SpyGameBot"))
    owner_ids: List[int] = Field(default_factory=lambda: _get_id_list("OWNER_IDS"))

    # MongoDB
    mongo_uri: str = Field(
        default_factory=lambda: os.getenv("MONGO_URI", "mongodb://localhost:27017")
    )
    mongo_db_name: str = Field(
        default_factory=lambda: os.getenv("MONGO_DB_NAME", "spygame_bot")
    )
    mongo_max_pool: int = Field(default_factory=lambda: _get_int("MONGO_MAX_POOL", 100))
    mongo_min_pool: int = Field(default_factory=lambda: _get_int("MONGO_MIN_POOL", 10))

    # Game defaults
    default_min_players: int = Field(default_factory=lambda: _get_int("MIN_PLAYERS", 3))
    default_max_players: int = Field(default_factory=lambda: _get_int("MAX_PLAYERS", 12))
    lobby_countdown: int = Field(default_factory=lambda: _get_int("LOBBY_COUNTDOWN", 60))
    question_phase_seconds: int = Field(
        default_factory=lambda: _get_int("QUESTION_PHASE_SECONDS", 300)
    )
    discussion_phase_seconds: int = Field(
        default_factory=lambda: _get_int("DISCUSSION_PHASE_SECONDS", 120)
    )
    voting_phase_seconds: int = Field(
        default_factory=lambda: _get_int("VOTING_PHASE_SECONDS", 60)
    )

    # Anti-abuse
    rate_limit_window: int = Field(default_factory=lambda: _get_int("RATE_LIMIT_WINDOW", 5))
    rate_limit_max: int = Field(default_factory=lambda: _get_int("RATE_LIMIT_MAX", 8))
    daily_reward_cooldown: int = Field(
        default_factory=lambda: _get_int("DAILY_REWARD_COOLDOWN", 86400)
    )

    # Logging
    log_level: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    log_dir: str = Field(default_factory=lambda: os.getenv("LOG_DIR", "bot/logs"))

    # Scheduler
    timezone: str = Field(default_factory=lambda: os.getenv("TIMEZONE", "UTC"))

    # Misc
    debug: bool = Field(default_factory=lambda: _get_bool("DEBUG", False))
    avoid_recent_locations: int = Field(
        default_factory=lambda: _get_int("AVOID_RECENT_LOCATIONS", 30)
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings singleton."""
    return Settings()


settings = get_settings()
