"""Achievement evaluation and unlocking."""
from __future__ import annotations

import json
import os
from typing import Dict, List, Optional

from bot.database.repositories import UserRepository
from bot.services.reward_service import RewardService
from bot.utils.logger import get_logger

log = get_logger(__name__)


class AchievementService:
    """Tracks achievement definitions and unlocks them based on user stats."""

    def __init__(
        self,
        users: UserRepository,
        rewards: RewardService,
        data_path: Optional[str] = None,
    ) -> None:
        self._users = users
        self._rewards = rewards
        self._data_path = data_path or os.path.join(
            os.path.dirname(__file__), "..", "data", "achievements.json"
        )
        self._definitions: List[Dict] = []
        self._load()

    def _load(self) -> None:
        path = os.path.abspath(self._data_path)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self._definitions = data.get("achievements", [])
        log.info("Loaded %d achievement definitions.", len(self._definitions))

    def all(self) -> List[Dict]:
        return list(self._definitions)

    def get(self, code: str) -> Optional[Dict]:
        return next((a for a in self._definitions if a["code"] == code), None)

    async def check_and_unlock(self, user_id: int) -> List[Dict]:
        """Check all achievement thresholds for a user. Returns newly unlocked list."""
        user = await self._users.get(user_id)
        if not user:
            return []
        unlocked: List[Dict] = []
        for ach in self._definitions:
            if ach["code"] in user.achievements:
                continue
            metric = ach.get("metric")
            threshold = int(ach.get("threshold", 0))
            value = int(getattr(user, metric, 0)) if metric else 0
            if value >= threshold:
                added = await self._users.add_achievement(user_id, ach["code"])
                if added:
                    await self._rewards.grant(
                        user_id=user_id,
                        xp=int(ach.get("reward_xp", 0)),
                        coins=int(ach.get("reward_coins", 0)),
                        reason=f"achievement:{ach['code']}",
                    )
                    unlocked.append(ach)
        return unlocked
