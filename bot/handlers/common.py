"""Common helpers used by handlers."""
from __future__ import annotations

from typing import Optional

from telegram import Chat, Update, User
from telegram.ext import ContextTypes

from bot.config import settings
from bot.middleware.rate_limiter import get_rate_limiter
from bot.services.container import get_container
from bot.utils.logger import get_logger
from bot.utils.text import escape_md

log = get_logger(__name__)


def is_owner(user_id: int) -> bool:
    return user_id in settings.owner_ids


async def is_group_admin(update: Update, user_id: int) -> bool:
    chat = update.effective_chat
    if not chat or chat.type == Chat.PRIVATE:
        return False
    try:
        member = await chat.get_member(user_id)
        return member.status in {"administrator", "creator"}
    except Exception as exc:  # pragma: no cover
        log.warning("Failed to fetch member status: %s", exc)
        return False


async def rate_limited(update: Update, key_suffix: str = "") -> bool:
    """Return True if request should be dropped due to rate-limit."""
    user = update.effective_user
    if not user:
        return False
    limiter = get_rate_limiter()
    key = f"u:{user.id}:{key_suffix}" if key_suffix else f"u:{user.id}"
    return not await limiter.allow(key)


async def ensure_user_known(update: Update) -> None:
    user = update.effective_user
    if not user:
        return
    container = get_container()
    await container.users.get_or_create(
        user_id=user.id,
        username=user.username,
        full_name=user.full_name or "",
        language_code=user.language_code,
    )


async def reply_md(update: Update, text: str, **kwargs) -> None:
    if update.effective_message:
        await update.effective_message.reply_text(
            text, parse_mode="MarkdownV2", **kwargs
        )


def user_display(user: User) -> str:
    return user.full_name or (user.username or str(user.id))


def chat_display(chat: Optional[Chat]) -> str:
    if chat is None:
        return ""
    return chat.title or chat.full_name or str(chat.id)
