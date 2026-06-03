"""Profile, rank, leaderboard, achievement, mission, daily handlers."""
from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from bot.handlers.common import ensure_user_known, rate_limited
from bot.services.container import get_container
from bot.services.xp_service import progress
from bot.utils.text import escape_md, format_user_link
from bot.utils.time_utils import human_duration


async def cmd_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await rate_limited(update, "profile"):
        return
    user = update.effective_user
    if not user:
        return
    await ensure_user_known(update)
    container = get_container()
    profile = await container.users.get(user.id)
    if not profile:
        await update.effective_message.reply_text("No profile yet — play a game first!")
        return

    level, xp_into, xp_needed = progress(profile.xp)
    rank = await container.leaderboard.rank_of(user.id, "xp")
    achievements_count = len(profile.achievements)
    text = (
        f"👤 *Profile* — {format_user_link(profile.user_id, profile.full_name or 'Player')}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🏷️ Level: *{level}*\n"
        f"✨ XP: *{profile.xp}* \\({xp_into}/{xp_needed} to next\\)\n"
        f"🪙 Coins: *{profile.coins}*\n"
        f"🥇 Wins: *{profile.wins}*  •  💀 Losses: *{profile.losses}*  •  🤝 Draws: *{profile.draws}*\n"
        f"🎮 Games Played: *{profile.games_played}*\n"
        f"🕵️ Spy Wins: *{profile.spy_wins}*  •  👥 Civilian Wins: *{profile.civilian_wins}*\n"
        f"🎯 Correct Guesses: *{profile.correct_guesses}*  •  🗳️ Correct Votes: *{profile.correct_votes}*\n"
        f"🏆 Achievements: *{achievements_count}*\n"
        f"🌐 Global XP Rank: *\\#{rank}*\n"
        f"🔥 Daily Streak: *{profile.daily_streak}*"
    )
    await update.effective_message.reply_text(text, parse_mode="MarkdownV2")


async def cmd_rank(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await rate_limited(update, "rank"):
        return
    user = update.effective_user
    if not user:
        return
    container = get_container()
    xp_rank = await container.leaderboard.rank_of(user.id, "xp")
    wins_rank = await container.leaderboard.rank_of(user.id, "wins")
    coins_rank = await container.leaderboard.rank_of(user.id, "coins")
    text = (
        "📊 *Your Ranks*\n"
        f"✨ XP: \\#{xp_rank}\n"
        f"🥇 Wins: \\#{wins_rank}\n"
        f"🪙 Coins: \\#{coins_rank}"
    )
    await update.effective_message.reply_text(text, parse_mode="MarkdownV2")


async def cmd_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await rate_limited(update, "lb"):
        return
    container = get_container()
    top_xp = await container.leaderboard.top_xp(10)
    top_wins = await container.leaderboard.top_wins(10)
    top_seasonal = await container.leaderboard.top_seasonal_xp(5)

    def format_list(label: str, users, attr: str) -> str:
        lines = [f"*{label}*"]
        for idx, u in enumerate(users, 1):
            name = u.full_name or u.username or str(u.user_id)
            lines.append(f"{idx}\\. {escape_md(name)} — *{getattr(u, attr)}*")
        return "\n".join(lines) if users else f"*{label}*\n_No data yet_"

    text = (
        f"🏆 *Leaderboards*\n\n"
        f"{format_list('Top XP', top_xp, 'xp')}\n\n"
        f"{format_list('Top Wins', top_wins, 'wins')}\n\n"
        f"{format_list('Seasonal XP', top_seasonal, 'seasonal_xp')}"
    )
    await update.effective_message.reply_text(text, parse_mode="MarkdownV2")


async def cmd_top(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await cmd_leaderboard(update, context)


async def cmd_achievements(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await rate_limited(update, "ach"):
        return
    user = update.effective_user
    if not user:
        return
    await ensure_user_known(update)
    container = get_container()
    profile = await container.users.get(user.id)
    if not profile:
        await update.effective_message.reply_text("No profile yet — play a game first!")
        return
    unlocked = set(profile.achievements)
    all_ach = container.achievements.all()
    lines = ["🏆 *Achievements*"]
    for ach in all_ach:
        icon = ach.get("icon", "•")
        status = "✅" if ach["code"] in unlocked else "🔒"
        lines.append(
            f"{status} {icon} *{escape_md(ach['name'])}* — {escape_md(ach['description'])}"
        )
    await update.effective_message.reply_text(
        "\n".join(lines), parse_mode="MarkdownV2"
    )


async def cmd_missions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await rate_limited(update, "missions"):
        return
    user = update.effective_user
    if not user:
        return
    await ensure_user_known(update)
    container = get_container()
    grouped = await container.missions.list_for_user(user.id)
    lines = ["🎯 *Your Missions*"]
    for period in ("daily", "weekly"):
        lines.append(f"\n*{period.title()}*")
        items = grouped.get(period, [])
        if not items:
            lines.append("_None_")
            continue
        for entry in items:
            m = entry["mission"]
            state = "🏁" if entry["claimed"] else ("✅" if entry["completed"] else "•")
            lines.append(
                f"{state} *{escape_md(m.name)}* — {entry['progress']}/{entry['target']} "
                f"\\| 🎁 {m.reward_xp} XP \\+ {m.reward_coins} 🪙"
            )
    lines.append("\nClaim with `/claim mission_id`")
    await update.effective_message.reply_text("\n".join(lines), parse_mode="MarkdownV2")


async def cmd_claim(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await rate_limited(update, "claim"):
        return
    user = update.effective_user
    if not user or not context.args:
        await update.effective_message.reply_text("Usage: /claim mission_id")
        return
    mission_id = context.args[0].strip()
    container = get_container()
    mission = await container.missions.claim(user.id, mission_id)
    if not mission:
        await update.effective_message.reply_text(
            "Cannot claim — mission not completed or already claimed."
        )
        return
    await update.effective_message.reply_text(
        f"🎁 Claimed *{escape_md(mission.name)}*\\: "
        f"\\+{mission.reward_xp} XP, \\+{mission.reward_coins} coins\\!",
        parse_mode="MarkdownV2",
    )


async def cmd_daily(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await rate_limited(update, "daily"):
        return
    user = update.effective_user
    if not user:
        return
    await ensure_user_known(update)
    container = get_container()
    ok, xp, coins, streak, remaining = await container.daily_rewards.claim(user.id)
    if not ok:
        await update.effective_message.reply_text(
            f"⏳ You've already claimed today\\. Next reward in *{escape_md(human_duration(remaining or 0))}*\\.",
            parse_mode="MarkdownV2",
        )
        return
    await update.effective_message.reply_text(
        f"🎁 *Daily Reward Claimed\\!*\n\n"
        f"✨ \\+{xp} XP\n🪙 \\+{coins} Coins\n🔥 Streak: *{streak}*",
        parse_mode="MarkdownV2",
    )
