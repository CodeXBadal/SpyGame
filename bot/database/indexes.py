"""Index creation for all collections."""
from __future__ import annotations

from pymongo import ASCENDING, DESCENDING, IndexModel

from bot.database.mongodb import Database
from bot.utils.logger import get_logger

log = get_logger(__name__)


async def ensure_indexes(database: Database) -> None:
    """Create all required indexes idempotently."""
    db = database.db

    await db.users.create_indexes(
        [
            IndexModel([("user_id", ASCENDING)], unique=True, name="uniq_user_id"),
            IndexModel([("xp", DESCENDING)], name="xp_desc"),
            IndexModel([("coins", DESCENDING)], name="coins_desc"),
            IndexModel([("wins", DESCENDING)], name="wins_desc"),
            IndexModel([("seasonal_xp", DESCENDING)], name="season_xp_desc"),
            IndexModel([("seasonal_wins", DESCENDING)], name="season_wins_desc"),
        ]
    )

    await db.groups.create_indexes(
        [IndexModel([("group_id", ASCENDING)], unique=True, name="uniq_group_id")]
    )

    await db.games.create_indexes(
        [
            IndexModel([("game_id", ASCENDING)], unique=True, name="uniq_game_id"),
            IndexModel([("group_id", ASCENDING)], name="by_group"),
            IndexModel([("status", ASCENDING)], name="by_status"),
            IndexModel([("created_at", DESCENDING)], name="created_desc"),
        ]
    )

    await db.votes.create_indexes(
        [
            IndexModel(
                [("game_id", ASCENDING), ("voter_id", ASCENDING)],
                unique=True,
                name="uniq_game_voter",
            )
        ]
    )

    await db.economy.create_indexes(
        [
            IndexModel([("user_id", ASCENDING)], name="by_user"),
            IndexModel([("created_at", DESCENDING)], name="created_desc"),
        ]
    )

    await db.daily_rewards.create_indexes(
        [IndexModel([("user_id", ASCENDING)], unique=True, name="uniq_user")]
    )

    await db.missions.create_indexes(
        [IndexModel([("mission_id", ASCENDING)], unique=True, name="uniq_mission")]
    )

    await db.mission_progress.create_indexes(
        [
            IndexModel(
                [
                    ("user_id", ASCENDING),
                    ("mission_id", ASCENDING),
                    ("period_key", ASCENDING),
                ],
                unique=True,
                name="uniq_user_mission_period",
            )
        ]
    )

    await db.seasons.create_indexes(
        [
            IndexModel([("season_id", ASCENDING)], unique=True, name="uniq_season"),
            IndexModel([("active", ASCENDING)], name="by_active"),
        ]
    )

    await db.audit_logs.create_indexes(
        [
            IndexModel([("created_at", DESCENDING)], name="created_desc"),
            IndexModel([("action", ASCENDING)], name="by_action"),
            IndexModel([("group_id", ASCENDING)], name="by_group"),
        ]
    )

    await db.achievements.create_indexes(
        [IndexModel([("code", ASCENDING)], unique=True, name="uniq_code")]
    )

    await db.cooldowns.create_indexes(
        [
            IndexModel(
                [("user_id", ASCENDING), ("key", ASCENDING)],
                unique=True,
                name="uniq_user_key",
            ),
            IndexModel(
                [("expires_at", ASCENDING)],
                expireAfterSeconds=0,
                name="ttl_expires",
            ),
        ]
    )

    log.info("MongoDB indexes ensured.")
