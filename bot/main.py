"""Bot bootstrap and lifecycle."""
from __future__ import annotations

import asyncio
import signal
import sys

from telegram.ext import Application, ApplicationBuilder

from bot.cache.cache_manager import get_cache
from bot.config import settings
from bot.database.indexes import ensure_indexes
from bot.database.mongodb import get_database
from bot.handlers.registration import register_handlers
from bot.middleware.rate_limiter import get_rate_limiter
from bot.scheduler.scheduler import BotScheduler
from bot.services.container import get_container
from bot.utils.logger import get_logger, setup_logging


async def _bootstrap() -> tuple[Application, BotScheduler]:
    """Initialize DB, container, scheduler, build Application."""
    log = get_logger(__name__)

    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN missing. Set it in your .env file.")

    db = get_database()
    await db.connect()
    await ensure_indexes(db)

    container = get_container()
    await container.seasons.ensure_active()
    await container.missions.seed_from_file()

    # Recover active games on restart: log + ensure caches
    active_games = await container.games_repo.list_active()
    log.info("Recovered %d active games from MongoDB.", len(active_games))
    for game in active_games:
        await container.cache.set(
            f"game:active:{game.group_id}", game, ttl=3600
        )

    app = (
        ApplicationBuilder()
        .token(settings.bot_token)
        .concurrent_updates(True)
        .build()
    )
    register_handlers(app)

    scheduler = BotScheduler(
        container=container,
        rate_limiter=get_rate_limiter(),
        cache=get_cache(),
    )
    return app, scheduler


async def _run() -> None:
    setup_logging()
    log = get_logger("bot.main")
    app, scheduler = await _bootstrap()

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    def _shutdown_signal(*_args) -> None:
        log.info("Shutdown signal received.")
        stop_event.set()

    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, _shutdown_signal)
        except (NotImplementedError, RuntimeError):  # pragma: no cover
            signal.signal(sig, _shutdown_signal)

    await app.initialize()
    await app.start()
    scheduler.start()
    await app.updater.start_polling(
        allowed_updates=[
            "message",
            "edited_message",
            "callback_query",
            "my_chat_member",
            "chat_member",
        ],
        drop_pending_updates=False,
    )
    log.info("✅ Bot is running. Press Ctrl+C to stop.")

    try:
        await stop_event.wait()
    finally:
        log.info("Stopping bot...")
        scheduler.shutdown()
        try:
            await app.updater.stop()
        except Exception:  # pragma: no cover
            pass
        await app.stop()
        await app.shutdown()
        await get_database().disconnect()
        log.info("Bot shut down cleanly.")


def main() -> None:
    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
