"""Tests for text utilities."""
from bot.utils.text import escape_md, format_user_link


def test_escape_md_basic() -> None:
    raw = "Hello_World!"
    out = escape_md(raw)
    assert "\\_" in out
    assert "\\!" in out


def test_escape_md_handles_none() -> None:
    assert escape_md(None) == ""


def test_user_link_escapes() -> None:
    link = format_user_link(42, "Alice.")
    assert "tg://user?id=42" in link
    assert "Alice\\." in link
