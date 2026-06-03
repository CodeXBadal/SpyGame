"""Start, help, ping, error handlers."""
from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from bot.handlers.common import ensure_user_known, rate_limited
from bot.utils.logger import get_logger
from bot.utils.text import escape_md

log = get_logger(__name__)


HELP_TEXT = (
    "🕵️ *Spy Game Bot — Help*\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "*Game*\n"
    "`/spy` or `/startgame` — start a lobby in a group\n"
    "`/join` — join the lobby\n"
    "`/leave` — leave the lobby\n"
    "`/forcestart` — start immediately \\(host/admin\\)\n"
    "`/cancelgame` — cancel \\(host/admin\\)\n"
    "`/ask @user question` — ask a question\n"
    "`/next` — pass the turn\n"
    "`/vote` — open voting\n"
    "`/guess LOCATION` — Spy guess\n\n"
    "*Profile & Stats*\n"
    "`/profile` `/rank` `/leaderboard` `/top` `/achievements`\n\n"
    "*Economy*\n"
    "`/daily` `/missions` `/claim <id>`\n\n"
    "*Admin*\n"
    "`/admin` `/setminplayers` `/setmaxplayers` `/settimer` `/setlanguage` `/forcestop`"
)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await rate_limited(update, "start"):
        return
    await ensure_user_known(update)
    user = update.effective_user
    name = user.full_name if user else "player"
    text = (
        f"👋 Hi {escape_md(name)}\\!\n\n"
        "I'm a *Spy Game* bot for Telegram groups\\.\n"
        "Add me to a group and start with `/spy` or `/startgame`\\.\n\n"
        "Use `/help` to see all commands\\."
    )
    await update.effective_message.reply_text(text, parse_mode="MarkdownV2")


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await rate_limited(update, "help"):
        return
    await update.effective_message.reply_text(HELP_TEXT, parse_mode="MarkdownV2")


async def cmd_ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text("🏓 pong")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    log.error("Unhandled exception", exc_info=context.error)
