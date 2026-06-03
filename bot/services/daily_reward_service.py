"""Daily reward claiming with streak tracking."""
from __future__ import annotations

import random
from datetime import timedelta
from typing import Optional, Tuple

from bot.config import settings
from bot.database.repositories import UserRepository
from bot.services.reward_service import RewardService
from bot.utils.time_utils import utcnow


class DailyRewardService:
    def __init__(self, users: UserRepository, rewards: RewardService) -> None:
        self._users = users
        self._rewards = rewards

    async def claim(self, user_id: int) -> Tuple[bool, int, int, int, Optional[int]]:
        """
        Try to claim daily reward.
        Returns (success, xp, coins, streak, seconds_until_next_if_blocked).
        """
        user = await self._users.get(user_id)
        if not user:
            return False, 0, 0, 0, None
        now = utcnow()
        cooldown = settings.daily_reward_cooldown
        if user.last_daily_at:
            last = user.last_daily_at
            if last.tzinfo is None:
                from datetime import timezone
                last = last.replace(tzinfo=timezone.utc)
            delta = (now - last).total_seconds()
            if delta < cooldown:
                remaining = int(cooldown - delta)
                return False, 0, 0, user.daily_streak, remaining
            # Streak continues only if claimed within 48h, else reset.
            streak = user.daily_streak + 1 if delta < cooldown * 2 else 1
        else:
            streak = 1

        base_xp = 25
        base_coins = 50
        bonus = min(streak - 1, 9) * 10
        random_bonus = random.randint(0, 25)
        xp = base_xp + bonus
        coins = base_coins + bonus + random_bonus

        await self._users.set_daily(user_id, now, streak)
        await self._rewards.grant(
            user_id=user_id, xp=xp, coins=coins, reason="daily_reward"
        )
        return True, xp, coins, streak, None
