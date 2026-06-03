"""Bot-owner only commands."""
from __future__ import annotations

import asyncio
from typing import Optional

from telegram import Update
from telegram.error import TelegramError
from telegram.ext import ContextTypes

from bot.handlers.common import is_owner
from bot.services.container import get_container
from bot.utils.logger import get_logger
from bot.utils.text import escape_md

log = get_logger(__name__)


async def _require_owner(update: Update) -> bool:
    user = update.effective_user
    if not user or not is_owner(user.id):
        if update.effective_message:
            await update.effective_message.reply_text("❌ Owner only.")
        return False
    return True


async def cmd_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_owner(update):
        return
    if not context.args:
        await update.effective_message.reply_text("Usage: /broadcast <message>")
        return
    text = " ".join(context.args)
    container = get_container()
    cursor = container.groups._col.find({}, {"group_id": 1})  # noqa: SLF001
    sent = 0
    failed = 0
    async for doc in cursor:
        try:
            await context.bot.send_message(doc["group_id"], text)
            sent += 1
        except TelegramError:
            failed += 1
        await asyncio.sleep(0.05)
    await update.effective_message.reply_text(
        f"📣 Broadcast complete. Sent: {sent}, Failed: {failed}"
    )


async def cmd_usercount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_owner(update):
        return
    container = get_container()
    total = await container.users.count()
    await update.effective_message.reply_text(f"👥 Total users: {total}")


async def cmd_groupcount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_owner(update):
        return
    container = get_container()
    total = await container.groups.count()
    await update.effective_message.reply_text(f"💬 Total groups: {total}")


async def cmd_gamecount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_owner(update):
        return
    container = get_container()
    total = await container.games_repo.count_total()
    active = await container.games_repo.count_active()
    await update.effective_message.reply_text(
        f"🎮 Games total: {total}\n▶️ Active: {active}"
    )


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_owner(update):
        return
    container = get_container()
    users = await container.users.count()
    groups = await container.groups.count()
    total_games = await container.games_repo.count_total()
    active_games = await container.games_repo.count_active()
    healthy = await container.database.health_check()
    text = (
        "📊 *Bot Stats*\n"
        f"DB healthy: *{'✅' if healthy else '❌'}*\n"
        f"Users: *{users}*\n"
        f"Groups: *{groups}*\n"
        f"Total Games: *{total_games}*\n"
        f"Active Games: *{active_games}*"
    )
    await update.effective_message.reply_text(text, parse_mode="MarkdownV2")
