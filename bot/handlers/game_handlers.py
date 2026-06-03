"""Game-related command handlers."""
from __future__ import annotations

from telegram import Chat, Update
from telegram.error import Forbidden, TelegramError
from telegram.ext import ContextTypes

from bot.handlers.common import (
    chat_display,
    ensure_user_known,
    is_group_admin,
    rate_limited,
)
from bot.keyboards.lobby_kb import lobby_keyboard, voting_keyboard
from bot.models.game import GamePhase, GameStatus, PlayerModel, Role
from bot.services.container import get_container
from bot.utils.logger import get_logger
from bot.utils.text import escape_md, format_user_link

log = get_logger(__name__)


# --------- helpers ---------
def _is_group(chat: Chat) -> bool:
    return chat.type in {Chat.GROUP, Chat.SUPERGROUP}


def _format_lobby_text(game) -> str:
    lines = [
        "🕵️ *Spy Game Lobby*",
        "",
        f"Players: *{game.player_count}/{game.max_players}* \\(min {game.min_players}\\)",
        "",
    ]
    if game.players:
        lines.append("*Joined:*")
        for p in game.players.values():
            lines.append(f"• {format_user_link(p.user_id, p.full_name or p.username or str(p.user_id))}")
    else:
        lines.append("_No players yet_")
    lines.append("")
    lines.append("Tap *Join* to enter the lobby\\.")
    return "\n".join(lines)


async def _deliver_role(context: ContextTypes.DEFAULT_TYPE, game, player) -> bool:
    text = (
        f"🕵️ *Spy Game — Group:* {escape_md(str(game.group_id))}\n\n"
        f"You are the *SPY*\\!\nGuess the location with `/guess LOCATION` to win\\."
        if player.role == Role.SPY
        else (
            f"🕵️ *Spy Game — Group:* {escape_md(str(game.group_id))}\n\n"
            f"Your location is: *{escape_md(game.location)}*\n"
            f"Don't reveal it — find the spy\\!"
        )
    )
    try:
        await context.bot.send_message(player.user_id, text, parse_mode="MarkdownV2")
        return True
    except Forbidden:
        return False
    except TelegramError as exc:
        log.warning("Failed to DM user %s: %s", player.user_id, exc)
        return False


# --------- commands ---------
async def cmd_spy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await cmd_startgame(update, context)


async def cmd_startgame(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await rate_limited(update, "startgame"):
        return
    chat = update.effective_chat
    user = update.effective_user
    if not chat or not user:
        return
    if not _is_group(chat):
        await update.effective_message.reply_text(
            "❌ This command works only in groups."
        )
        return
    await ensure_user_known(update)
    container = get_container()
    game, error = await container.game.create_lobby(
        group_id=chat.id, group_title=chat.title, host_id=user.id
    )
    if error or not game:
        await update.effective_message.reply_text(f"⚠️ {error}")
        return

    # Auto-join host directly (calling join() would deadlock — same lock)
    game.players[str(user.id)] = PlayerModel(
        user_id=user.id,
        username=user.username,
        full_name=user.full_name or "",
    )
    await container.game._persist(game)

    sent = await update.effective_message.reply_text(
        _format_lobby_text(game),
        parse_mode="MarkdownV2",
        reply_markup=lobby_keyboard(game.game_id),
    )
    game.lobby_message_id = sent.message_id
    await container.game._persist(game)


async def cmd_join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await rate_limited(update, "join"):
        return
    chat = update.effective_chat
    user = update.effective_user
    if not chat or not user or not _is_group(chat):
        return
    await ensure_user_known(update)
    container = get_container()
    game, error = await container.game.join(
        chat.id, user.id, user.username, user.full_name or ""
    )
    if error:
        await update.effective_message.reply_text(f"⚠️ {error}")
        return
    if game:
        await _refresh_lobby_message(context, game)


async def cmd_leave(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await rate_limited(update, "leave"):
        return
    chat = update.effective_chat
    user = update.effective_user
    if not chat or not user or not _is_group(chat):
        return
    container = get_container()
    game, error = await container.game.leave(chat.id, user.id)
    if error:
        await update.effective_message.reply_text(f"⚠️ {error}")
        return
    if game:
        await _refresh_lobby_message(context, game)


async def cmd_cancelgame(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await rate_limited(update, "cancel"):
        return
    chat = update.effective_chat
    user = update.effective_user
    if not chat or not user or not _is_group(chat):
        return
    container = get_container()
    force = await is_group_admin(update, user.id)
    ok, error = await container.game.cancel(chat.id, user.id, force=force)
    if not ok:
        await update.effective_message.reply_text(f"⚠️ {error}")
        return
    await update.effective_message.reply_text("🛑 Game cancelled.")


async def cmd_forcestart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await rate_limited(update, "forcestart"):
        return
    chat = update.effective_chat
    user = update.effective_user
    if not chat or not user or not _is_group(chat):
        return
    container = get_container()
    force = await is_group_admin(update, user.id)
    game, error = await container.game.start_game(chat.id, user.id, force=force)
    if error or not game:
        await update.effective_message.reply_text(f"⚠️ {error}")
        return
    await _announce_game_start(context, game)


async def _announce_game_start(context: ContextTypes.DEFAULT_TYPE, game) -> None:
    container = get_container()
    sent_roles = 0
    failed = []
    for player in game.players.values():
        ok = await _deliver_role(context, game, player)
        if ok:
            sent_roles += 1
        else:
            failed.append(player)
            player.dm_ok = False
    await container.game._persist(game)

    asker = game.get_player(game.current_asker_id) if game.current_asker_id else None
    asker_mention = (
        format_user_link(asker.user_id, asker.full_name or "Player")
        if asker
        else "_someone_"
    )
    text = (
        "🚨 *Game Started\\!*\n\n"
        f"Roles have been sent in *DM* to {sent_roles}/{len(game.players)} players\\.\n"
    )
    if failed:
        text += "\n⚠️ Could not DM: " + ", ".join(
            format_user_link(p.user_id, p.full_name or "Player") for p in failed
        )
        text += "\nPlease start a chat with me and re\\-run /forcestart\\.\n"

    text += (
        "\n🎤 *Question Phase*\n"
        f"It is {asker_mention}'s turn to ask\\.\n"
        "Use `/ask @user your question` or `/next` to pass\\.\n"
        "Spy can guess any time with `/guess LOCATION`\\.\n"
        "Move on with `/vote` when ready\\."
    )
    await context.bot.send_message(
        game.group_id, text, parse_mode="MarkdownV2"
    )


async def _refresh_lobby_message(context: ContextTypes.DEFAULT_TYPE, game) -> None:
    if not game.lobby_message_id:
        return
    try:
        await context.bot.edit_message_text(
            chat_id=game.group_id,
            message_id=game.lobby_message_id,
            text=_format_lobby_text(game),
            parse_mode="MarkdownV2",
            reply_markup=lobby_keyboard(game.game_id),
        )
    except TelegramError:
        pass  # message was deleted/edited concurrently


# --------- question phase ---------
async def cmd_ask(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await rate_limited(update, "ask"):
        return
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message
    if not chat or not user or not msg or not _is_group(chat):
        return
    if not context.args:
        await msg.reply_text("Usage: /ask @username Your question")
        return

    target_id = None
    # Resolve target: prefer reply, then @mention entity, then first arg as @username
    if msg.reply_to_message and msg.reply_to_message.from_user:
        target_id = msg.reply_to_message.from_user.id
        question = " ".join(context.args)
    else:
        question_parts = list(context.args)
        first = question_parts[0]
        target_username = first.lstrip("@")
        container = get_container()
        game = await container.game.get_active(chat.id)
        if not game:
            await msg.reply_text("No active game.")
            return
        for p in game.players.values():
            if p.username and p.username.lower() == target_username.lower():
                target_id = p.user_id
                break
            if str(p.user_id) == target_username:
                target_id = p.user_id
                break
        question = " ".join(question_parts[1:]) if target_id else " ".join(question_parts)

    if target_id is None:
        await msg.reply_text("Could not find target player. Reply to them or use @username.")
        return
    if not question.strip():
        await msg.reply_text("Please include a question after the target.")
        return

    container = get_container()
    game, error = await container.game.record_question(
        chat.id, user.id, target_id, question
    )
    if error or not game:
        await msg.reply_text(f"⚠️ {error}")
        return
    target = game.get_player(target_id)
    asker = game.get_player(user.id)
    txt = (
        f"❓ {format_user_link(user.id, asker.full_name if asker else 'Player')} "
        f"asks {format_user_link(target_id, target.full_name if target else 'Player')}:\n"
        f"_{escape_md(question)}_\n\n"
        f"Now {format_user_link(target_id, target.full_name if target else 'Player')} answers, "
        f"then asks the next question with `/ask`\\."
    )
    await msg.reply_text(txt, parse_mode="MarkdownV2")


async def cmd_next(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await rate_limited(update, "next"):
        return
    chat = update.effective_chat
    user = update.effective_user
    if not chat or not user or not _is_group(chat):
        return
    container = get_container()
    game, error = await container.game.next_asker(chat.id, user.id)
    if error or not game:
        await update.effective_message.reply_text(f"⚠️ {error}")
        return
    asker = game.get_player(game.current_asker_id) if game.current_asker_id else None
    if asker:
        await update.effective_message.reply_text(
            f"➡️ Now it's {format_user_link(asker.user_id, asker.full_name or 'Player')}'s turn to ask\\.",
            parse_mode="MarkdownV2",
        )


# --------- guess ---------
async def cmd_guess(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await rate_limited(update, "guess"):
        return
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message
    if not chat or not user or not msg or not _is_group(chat):
        return
    if not context.args:
        await msg.reply_text("Usage: /guess LOCATION_NAME")
        return
    guess_text = " ".join(context.args).strip()
    container = get_container()
    game, correct, error = await container.game.spy_guess(chat.id, user.id, guess_text)
    if error:
        await msg.reply_text(f"⚠️ {error}")
        return
    if not game:
        return
    if correct:
        text = (
            "🎯 *SPY GUESSED CORRECTLY\\!*\n\n"
            f"The location was *{escape_md(game.location)}*\\.\n"
            f"🏆 Spy wins\\!\n"
        )
    else:
        text = (
            "💥 *SPY GUESSED WRONG\\!*\n\n"
            f"The location was *{escape_md(game.location)}*\\.\n"
            f"🏆 Civilians win\\!\n"
        )
    await msg.reply_text(text, parse_mode="MarkdownV2")


# --------- vote ---------
async def cmd_vote(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await rate_limited(update, "vote"):
        return
    chat = update.effective_chat
    user = update.effective_user
    if not chat or not user or not _is_group(chat):
        return
    container = get_container()
    game = await container.game.get_active(chat.id)
    if not game or game.status != GameStatus.RUNNING:
        await update.effective_message.reply_text("No running game.")
        return
    if game.phase != GamePhase.VOTING:
        # Promote to voting phase
        game = await container.game.advance_to_voting(chat.id)
        if not game:
            await update.effective_message.reply_text("Could not enter voting phase.")
            return
    candidates = [
        (p.user_id, p.full_name or p.username or str(p.user_id))
        for p in game.players.values()
        if p.is_alive
    ]
    await update.effective_message.reply_text(
        "🗳️ *Vote for the suspected Spy*",
        parse_mode="MarkdownV2",
        reply_markup=voting_keyboard(game.game_id, candidates),
    )
