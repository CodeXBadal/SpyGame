"""Inline button (callback query) handlers."""
from __future__ import annotations

from telegram import Update
from telegram.error import TelegramError
from telegram.ext import ContextTypes

from bot.handlers.common import ensure_user_known, is_group_admin
from bot.handlers.game_handlers import (
    _announce_game_start,
    _format_lobby_text,
    _refresh_lobby_message,
)
from bot.keyboards.lobby_kb import lobby_keyboard
from bot.models.game import GamePhase, GameStatus
from bot.services.container import get_container
from bot.utils.logger import get_logger
from bot.utils.text import escape_md, format_user_link

log = get_logger(__name__)


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query or not query.data:
        return
    await ensure_user_known(update)
    data = query.data
    parts = data.split(":")
    action = parts[0]

    try:
        if action == "lobby":
            await _handle_lobby(update, context, parts)
        elif action == "vote":
            await _handle_vote(update, context, parts)
        elif action == "confirm":
            await _handle_confirm(update, context, parts)
        else:
            await query.answer("Unknown action.")
    except Exception as exc:  # pragma: no cover
        log.exception("Callback error: %s", exc)
        try:
            await query.answer("⚠️ Error processing action.")
        except TelegramError:
            pass


async def _handle_lobby(update: Update, context: ContextTypes.DEFAULT_TYPE, parts) -> None:
    query = update.callback_query
    if len(parts) < 3:
        await query.answer()
        return
    _, sub, game_id = parts[0], parts[1], parts[2]
    user = update.effective_user
    chat = update.effective_chat
    container = get_container()
    if not chat or not user:
        await query.answer()
        return
    game = await container.game.get_active(chat.id)
    if not game or game.game_id != game_id:
        await query.answer("This lobby is no longer available.", show_alert=True)
        return

    if sub == "join":
        game, error = await container.game.join(
            chat.id, user.id, user.username, user.full_name or ""
        )
        if error:
            await query.answer(error, show_alert=True)
        else:
            await query.answer("Joined!")
            if game:
                await _refresh_lobby_message(context, game)
    elif sub == "leave":
        game, error = await container.game.leave(chat.id, user.id)
        if error:
            await query.answer(error, show_alert=True)
        else:
            await query.answer("Left.")
            if game:
                await _refresh_lobby_message(context, game)
    elif sub == "force":
        force = await is_group_admin(update, user.id)
        game, error = await container.game.start_game(chat.id, user.id, force=force)
        if error or not game:
            await query.answer(error or "Cannot start.", show_alert=True)
            return
        await query.answer("Starting...")
        try:
            await context.bot.edit_message_reply_markup(
                chat_id=chat.id, message_id=query.message.message_id, reply_markup=None
            )
        except TelegramError:
            pass
        await _announce_game_start(context, game)
    elif sub == "cancel":
        force = await is_group_admin(update, user.id)
        ok, error = await container.game.cancel(chat.id, user.id, force=force)
        if not ok:
            await query.answer(error or "Cannot cancel.", show_alert=True)
            return
        await query.answer("Cancelled.")
        try:
            await context.bot.edit_message_text(
                chat_id=chat.id,
                message_id=query.message.message_id,
                text="🛑 Lobby cancelled.",
            )
        except TelegramError:
            pass
    else:
        await query.answer()


async def _handle_vote(update: Update, context: ContextTypes.DEFAULT_TYPE, parts) -> None:
    query = update.callback_query
    if len(parts) < 3:
        await query.answer()
        return
    _, game_id, target_id = parts[0], parts[1], parts[2]
    user = update.effective_user
    chat = update.effective_chat
    if not user or not chat:
        await query.answer()
        return
    container = get_container()
    game = await container.game.get_active(chat.id)
    if not game or game.game_id != game_id:
        await query.answer("Vote expired.", show_alert=True)
        return

    try:
        target_uid = int(target_id)
    except ValueError:
        await query.answer("Invalid target.", show_alert=True)
        return

    game, error = await container.game.cast_vote(chat.id, user.id, target_uid)
    if error or not game:
        await query.answer(error or "Vote failed.", show_alert=True)
        return
    await query.answer("✅ Vote recorded.")
    # If everyone alive has voted, resolve immediately
    if len(game.votes) >= len(game.alive_player_ids):
        await context.bot.send_message(
            chat.id, "📊 All votes cast — tallying results...",
        )
        game, _ = await container.game.resolve_votes(chat.id)
        if game:
            await _announce_result(context, game)


async def _handle_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE, parts) -> None:
    query = update.callback_query
    await query.answer()


async def _announce_result(context: ContextTypes.DEFAULT_TYPE, game) -> None:
    winner_text = {
        "spy": "🕵️ *Spy Wins\\!*",
        "civilians": "👥 *Civilians Win\\!*",
        "draw": "🤝 *Draw\\!*",
    }.get(game.winner, "Game ended.")
    spy = game.get_player(game.spy_id) if game.spy_id else None
    spy_mention = (
        format_user_link(spy.user_id, spy.full_name or "Spy") if spy else "_unknown_"
    )
    text = (
        f"{winner_text}\n\n"
        f"Location: *{escape_md(game.location or 'Unknown')}*\n"
        f"Spy: {spy_mention}\n\n"
        f"Rewards have been distributed\\. Use `/profile` to view your stats\\."
    )
    await context.bot.send_message(
        game.group_id, text, parse_mode="MarkdownV2"
    )
