"""Inline keyboards for lobby, voting and confirmations."""
from __future__ import annotations

from typing import Iterable, Tuple

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def lobby_keyboard(game_id: str) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton("✅ Join", callback_data=f"lobby:join:{game_id}"),
            InlineKeyboardButton("❌ Leave", callback_data=f"lobby:leave:{game_id}"),
        ],
        [
            InlineKeyboardButton("▶️ Force Start", callback_data=f"lobby:force:{game_id}"),
            InlineKeyboardButton("🛑 Cancel", callback_data=f"lobby:cancel:{game_id}"),
        ],
    ]
    return InlineKeyboardMarkup(rows)


def voting_keyboard(
    game_id: str, candidates: Iterable[Tuple[int, str]]
) -> InlineKeyboardMarkup:
    rows = []
    buffer = []
    for uid, name in candidates:
        label = name[:18] if name else str(uid)
        buffer.append(
            InlineKeyboardButton(f"🗳️ {label}", callback_data=f"vote:{game_id}:{uid}")
        )
        if len(buffer) == 2:
            rows.append(buffer)
            buffer = []
    if buffer:
        rows.append(buffer)
    return InlineKeyboardMarkup(rows)


def confirm_cancel_keyboard(game_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ Confirm", callback_data=f"confirm:cancel:{game_id}"
                ),
                InlineKeyboardButton(
                    "❌ Back", callback_data=f"confirm:back:{game_id}"
                ),
            ]
        ]
    )
