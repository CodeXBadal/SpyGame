"""Season lifecycle management."""
from __future__ import annotations

from typing import Optional

from bot.database.repositories import SeasonRepository, UserRepository
from bot.models.season import SeasonModel
from bot.utils.logger import get_logger
from bot.utils.time_utils import utcnow

log = get_logger(__name__)


class SeasonService:
    def __init__(self, seasons: SeasonRepository, users: UserRepository) -> None:
        self._seasons = seasons
        self._users = users

    async def ensure_active(self) -> SeasonModel:
        active = await self._seasons.get_active()
        if active:
            return active
        now = utcnow()
        season_id = now.strftime("S%Y%m")
        name = now.strftime("Season %B %Y")
        season = SeasonModel(season_id=season_id, name=name)
        await self._seasons.create(season)
        log.info("Created new active season: %s", season_id)
        return season

    async def rollover(self) -> SeasonModel:
        """End current season and start a new one. Reset seasonal stats."""
        await self._seasons.deactivate_all()
        new_season = await self.ensure_active()
        modified = await self._users.reset_seasonal(new_season.season_id)
        log.info("Season rollover: reset seasonal stats for %d users.", modified)
        return new_season
