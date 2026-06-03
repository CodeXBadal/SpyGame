"""APScheduler integration for periodic maintenance tasks."""
from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from bot.cache.cache_manager import CacheManager
from bot.config import settings
from bot.middleware.rate_limiter import RateLimiter
from bot.services.container import ServiceContainer
from bot.utils.logger import get_logger

log = get_logger(__name__)


class BotScheduler:
    """Wraps APScheduler with the bot's recurring jobs."""

    def __init__(
        self,
        container: ServiceContainer,
        rate_limiter: RateLimiter,
        cache: CacheManager,
    ) -> None:
        self._container = container
        self._rate_limiter = rate_limiter
        self._cache = cache
        self._scheduler = AsyncIOScheduler(timezone=settings.timezone)

    def start(self) -> None:
        self._scheduler.add_job(
            self._job_cache_cleanup,
            IntervalTrigger(minutes=5),
            id="cache_cleanup",
            replace_existing=True,
        )
        self._scheduler.add_job(
            self._job_rate_limiter_cleanup,
            IntervalTrigger(minutes=10),
            id="rate_cleanup",
            replace_existing=True,
        )
        self._scheduler.add_job(
            self._job_expired_games_cleanup,
            IntervalTrigger(minutes=2),
            id="expired_games",
            replace_existing=True,
        )
        self._scheduler.add_job(
            self._job_season_check,
            CronTrigger(day=1, hour=0, minute=5),
            id="season_rollover",
            replace_existing=True,
        )
        self._scheduler.add_job(
            self._job_stats_log,
            IntervalTrigger(hours=1),
            id="stats_log",
            replace_existing=True,
        )
        self._scheduler.start()
        log.info("Scheduler started.")

    def shutdown(self) -> None:
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            log.info("Scheduler stopped.")

    # ---------- jobs ----------
    async def _job_cache_cleanup(self) -> None:
        removed = await self._cache.cleanup()
        if removed:
            log.info("Cache cleanup removed %d entries.", removed)

    async def _job_rate_limiter_cleanup(self) -> None:
        removed = await self._rate_limiter.cleanup()
        if removed:
            log.debug("Rate limiter pruned %d timestamps.", removed)

    async def _job_expired_games_cleanup(self) -> None:
        active = await self._container.games_repo.list_active()
        from bot.utils.time_utils import utcnow

        now = utcnow()
        for game in active:
            deadline = game.phase_deadline
            if not deadline:
                continue
            # Grace of 5 minutes past deadline → finalize as timeout/cancel
            if deadline.tzinfo is None:
                from datetime import timezone

                deadline = deadline.replace(tzinfo=timezone.utc)
            if (now - deadline).total_seconds() > 300:
                log.warning(
                    "Auto-finalizing stale game %s in group %s",
                    game.game_id,
                    game.group_id,
                )
                from bot.models.game import GameStatus

                if game.status == GameStatus.LOBBY.value or game.status == "lobby":
                    await self._container.games_repo.cancel_game(game.game_id)
                else:
                    await self._container.game.force_finalize_timeout(game.group_id)

    async def _job_season_check(self) -> None:
        await self._container.seasons.rollover()

    async def _job_stats_log(self) -> None:
        total_users = await self._container.users.count()
        total_groups = await self._container.groups.count()
        total_games = await self._container.games_repo.count_total()
        active_games = await self._container.games_repo.count_active()
        log.info(
            "Stats: users=%d groups=%d games=%d active=%d cache=%d",
            total_users,
            total_groups,
            total_games,
            active_games,
            await self._cache.size(),
        )
