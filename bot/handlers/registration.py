"""Register all handlers on the application."""
from __future__ import annotations

from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
)

from bot.handlers import (
    admin_handlers,
    callback_handlers,
    game_handlers,
    general_handlers,
    owner_handlers,
    profile_handlers,
)


def register_handlers(app: Application) -> None:
    # General
    app.add_handler(CommandHandler("start", general_handlers.cmd_start))
    app.add_handler(CommandHandler("help", general_handlers.cmd_help))
    app.add_handler(CommandHandler("ping", general_handlers.cmd_ping))

    # Game
    app.add_handler(CommandHandler("spy", game_handlers.cmd_spy))
    app.add_handler(CommandHandler("startgame", game_handlers.cmd_startgame))
    app.add_handler(CommandHandler("join", game_handlers.cmd_join))
    app.add_handler(CommandHandler("leave", game_handlers.cmd_leave))
    app.add_handler(CommandHandler("cancelgame", game_handlers.cmd_cancelgame))
    app.add_handler(CommandHandler("forcestart", game_handlers.cmd_forcestart))
    app.add_handler(CommandHandler("ask", game_handlers.cmd_ask))
    app.add_handler(CommandHandler("next", game_handlers.cmd_next))
    app.add_handler(CommandHandler("guess", game_handlers.cmd_guess))
    app.add_handler(CommandHandler("vote", game_handlers.cmd_vote))

    # Profile
    app.add_handler(CommandHandler("profile", profile_handlers.cmd_profile))
    app.add_handler(CommandHandler("rank", profile_handlers.cmd_rank))
    app.add_handler(CommandHandler("leaderboard", profile_handlers.cmd_leaderboard))
    app.add_handler(CommandHandler("top", profile_handlers.cmd_top))
    app.add_handler(CommandHandler("achievements", profile_handlers.cmd_achievements))
    app.add_handler(CommandHandler("missions", profile_handlers.cmd_missions))
    app.add_handler(CommandHandler("claim", profile_handlers.cmd_claim))
    app.add_handler(CommandHandler("daily", profile_handlers.cmd_daily))

    # Admin
    app.add_handler(CommandHandler("admin", admin_handlers.cmd_admin))
    app.add_handler(CommandHandler("setminplayers", admin_handlers.cmd_setminplayers))
    app.add_handler(CommandHandler("setmaxplayers", admin_handlers.cmd_setmaxplayers))
    app.add_handler(CommandHandler("settimer", admin_handlers.cmd_settimer))
    app.add_handler(CommandHandler("setlanguage", admin_handlers.cmd_setlanguage))
    app.add_handler(CommandHandler("forcestop", admin_handlers.cmd_forcestop))

    # Owner
    app.add_handler(CommandHandler("broadcast", owner_handlers.cmd_broadcast))
    app.add_handler(CommandHandler("usercount", owner_handlers.cmd_usercount))
    app.add_handler(CommandHandler("groupcount", owner_handlers.cmd_groupcount))
    app.add_handler(CommandHandler("gamecount", owner_handlers.cmd_gamecount))
    app.add_handler(CommandHandler("stats", owner_handlers.cmd_stats))

    # Callbacks
    app.add_handler(CallbackQueryHandler(callback_handlers.on_callback))

    # Error
    app.add_error_handler(general_handlers.error_handler)
