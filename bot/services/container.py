"""Dependency injection container: wires all services and repositories."""
from __future__ import annotations

from typing import Optional

from bot.cache.cache_manager import CacheManager, get_cache
from bot.database.mongodb import Database, get_database
from bot.database.repositories import (
    AuditRepository,
    CooldownRepository,
    EconomyRepository,
    GameRepository,
    GroupRepository,
    MissionRepository,
    SeasonRepository,
    UserRepository,
)
from bot.games.game_service import GameService
from bot.services.achievement_service import AchievementService
from bot.services.daily_reward_service import DailyRewardService
from bot.services.leaderboard_service import LeaderboardService
from bot.services.location_service import LocationService
from bot.services.mission_service import MissionService
from bot.services.reward_service import RewardService
from bot.services.season_service import SeasonService
from bot.utils.logger import get_logger

log = get_logger(__name__)


class ServiceContainer:
    """Holds wired repositories and services as a single graph."""

    def __init__(self, database: Database, cache: CacheManager) -> None:
        self.database = database
        self.cache = cache

        # Repositories
        self.users = UserRepository(database)
        self.groups = GroupRepository(database)
        self.games_repo = GameRepository(database)
        self.economy = EconomyRepository(database)
        self.audit = AuditRepository(database)
        self.missions_repo = MissionRepository(database)
        self.seasons_repo = SeasonRepository(database)
        self.cooldowns = CooldownRepository(database)

        # Services
        self.locations = LocationService()
        self.rewards = RewardService(self.users, self.economy, self.audit)
        self.achievements = AchievementService(self.users, self.rewards)
        self.missions = MissionService(self.missions_repo, self.rewards)
        self.daily_rewards = DailyRewardService(self.users, self.rewards)
        self.leaderboard = LeaderboardService(self.users)
        self.seasons = SeasonService(self.seasons_repo, self.users)
        self.game = GameService(
            games=self.games_repo,
            groups=self.groups,
            users=self.users,
            audit=self.audit,
            rewards=self.rewards,
            achievements=self.achievements,
            missions=self.missions,
            locations=self.locations,
            cache=self.cache,
        )


_container: Optional[ServiceContainer] = None


def get_container() -> ServiceContainer:
    global _container
    if _container is None:
        _container = ServiceContainer(database=get_database(), cache=get_cache())
    return _container
