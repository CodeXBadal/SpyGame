"""Reward distribution: XP, coins, level-ups, audit logging."""
from __future__ import annotations

from typing import Optional

from bot.database.repositories import (
    AuditRepository,
    EconomyRepository,
    UserRepository,
)
from bot.services.xp_service import level_for_xp
from bot.utils.logger import get_logger

log = get_logger(__name__)


class RewardService:
    """Apply XP/coin rewards atomically with audit + level updates."""

    def __init__(
        self,
        users: UserRepository,
        economy: EconomyRepository,
        audit: AuditRepository,
    ) -> None:
        self._users = users
        self._economy = economy
        self._audit = audit

    async def grant(
        self,
        user_id: int,
        xp: int = 0,
        coins: int = 0,
        reason: str = "",
        group_id: Optional[int] = None,
        game_id: Optional[str] = None,
    ) -> Optional[int]:
        """Apply rewards. Returns new level if a level-up occurred, else None."""
        if xp == 0 and coins == 0:
            return None
        await self._users.add_xp_coins(user_id, xp=xp, coins=coins)
        await self._economy.log(
            user_id=user_id,
            xp=xp,
            coins=coins,
            reason=reason,
            group_id=group_id,
            game_id=game_id,
        )
        await self._audit.log(
            action="reward",
            actor_id=user_id,
            group_id=group_id,
            game_id=game_id,
            payload={"xp": xp, "coins": coins, "reason": reason},
        )

        user = await self._users.get(user_id)
        if not user:
            return None
        new_level = level_for_xp(user.xp)
        if new_level != user.level:
            await self._users.set_level(user_id, new_level)
            log.info("User %s leveled up to %s", user_id, new_level)
            return new_level
        return None
