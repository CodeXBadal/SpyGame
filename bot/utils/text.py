"""Text helpers including MarkdownV2 escaping."""
from __future__ import annotations

from typing import Iterable

_MD_V2_SPECIAL = r"_*[]()~`>#+-=|{}.!\\"


def escape_md(text: object) -> str:
    """Escape a string for Telegram MarkdownV2."""
    s = "" if text is None else str(text)
    out = []
    for ch in s:
        if ch in _MD_V2_SPECIAL:
            out.append("\\" + ch)
        else:
            out.append(ch)
    return "".join(out)


def join_md(items: Iterable[str], sep: str = ", ") -> str:
    return sep.join(items)


def format_user_link(user_id: int, name: str) -> str:
    """Return a Markdown V2 inline mention link."""
    return f"[{escape_md(name)}](tg://user?id={int(user_id)})"
