"""Group admin commands."""
from __future__ import annotations

from telegram import Chat, Update
from telegram.ext import ContextTypes

from bot.handlers.common import is_group_admin, rate_limited
from bot.services.container import get_container
from bot.utils.text import escape_md


def _is_group(chat: Chat) -> bool:
    return chat.type in {Chat.GROUP, Chat.SUPERGROUP}


async def _require_admin(update: Update) -> bool:
    user = update.effective_user
    chat = update.effective_chat
    if not user or not chat or not _is_group(chat):
        await update.effective_message.reply_text("This command is for group admins.")
        return False
    if not await is_group_admin(update, user.id):
        await update.effective_message.reply_text("❌ You must be a group admin.")
        return False
    return True


async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await rate_limited(update, "admin"):
        return
    if not await _require_admin(update):
        return
    chat = update.effective_chat
    container = get_container()
    group = await container.groups.get_or_create(chat.id, title=chat.title)
    text = (
        "🛠️ *Admin Panel*\n"
        f"Min players: *{group.min_players}*\n"
        f"Max players: *{group.max_players}*\n"
        f"Lobby countdown: *{group.lobby_countdown}s*\n"
        f"Question phase: *{group.question_phase_seconds}s*\n"
        f"Discussion phase: *{group.discussion_phase_seconds}s*\n"
        f"Voting phase: *{group.voting_phase_seconds}s*\n"
        f"Language: *{escape_md(group.language)}*\n\n"
        "Commands: /setminplayers /setmaxplayers /settimer /setlanguage /forcestart /forcestop"
    )
    await update.effective_message.reply_text(text, parse_mode="MarkdownV2")


async def _parse_int_arg(context: ContextTypes.DEFAULT_TYPE) -> int | None:
    if not context.args:
        return None
    try:
        return int(context.args[0])
    except ValueError:
        return None


async def cmd_setminplayers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_admin(update):
        return
    value = await _parse_int_arg(context)
    if value is None or not (2 <= value <= 20):
        await update.effective_message.reply_text("Usage: /setminplayers 3 (2–20)")
        return
    container = get_container()
    await container.groups.update_settings(update.effective_chat.id, min_players=value)
    await update.effective_message.reply_text(f"✅ Min players set to {value}.")


async def cmd_setmaxplayers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_admin(update):
        return
    value = await _parse_int_arg(context)
    if value is None or not (3 <= value <= 30):
        await update.effective_message.reply_text("Usage: /setmaxplayers 12 (3–30)")
        return
    container = get_container()
    await container.groups.update_settings(update.effective_chat.id, max_players=value)
    await update.effective_message.reply_text(f"✅ Max players set to {value}.")


async def cmd_settimer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_admin(update):
        return
    if len(context.args) < 2:
        await update.effective_message.reply_text(
            "Usage: /settimer <phase> <seconds>\nPhases: lobby, question, discussion, voting"
        )
        return
    phase = context.args[0].lower()
    try:
        seconds = int(context.args[1])
    except ValueError:
        await update.effective_message.reply_text("Seconds must be a number.")
        return
    if not (10 <= seconds <= 1800):
        await update.effective_message.reply_text("Seconds must be 10–1800.")
        return
    mapping = {
        "lobby": "lobby_countdown",
        "question": "question_phase_seconds",
        "discussion": "discussion_phase_seconds",
        "voting": "voting_phase_seconds",
    }
    field = mapping.get(phase)
    if not field:
        await update.effective_message.reply_text("Unknown phase.")
        return
    container = get_container()
    await container.groups.update_settings(update.effective_chat.id, **{field: seconds})
    await update.effective_message.reply_text(f"✅ {phase} timer set to {seconds}s.")


async def cmd_setlanguage(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_admin(update):
        return
    if not context.args:
        await update.effective_message.reply_text("Usage: /setlanguage en")
        return
    lang = context.args[0].strip().lower()[:8]
    container = get_container()
    await container.groups.update_settings(update.effective_chat.id, language=lang)
    await update.effective_message.reply_text(f"✅ Language set to {lang}.")


async def cmd_forcestop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_admin(update):
        return
    chat = update.effective_chat
    user = update.effective_user
    container = get_container()
    ok, error = await container.game.cancel(chat.id, user.id, force=True)
    if not ok:
        await update.effective_message.reply_text(f"⚠️ {error}")
        return
    await update.effective_message.reply_text("🛑 Game force-stopped.")
