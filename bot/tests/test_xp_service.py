"""Tests for XP / level scaling."""
from bot.services.xp_service import level_for_xp, progress, threshold_for_level


def test_base_levels() -> None:
    assert level_for_xp(0) == 1
    assert level_for_xp(99) == 1
    assert level_for_xp(100) == 2
    assert level_for_xp(249) == 2
    assert level_for_xp(250) == 3
    assert level_for_xp(499) == 3
    assert level_for_xp(500) == 4


def test_high_levels_scale() -> None:
    lvl_low = level_for_xp(1_000)
    lvl_high = level_for_xp(1_000_000)
    assert lvl_high > lvl_low


def test_thresholds_monotonic() -> None:
    prev = -1
    for level in range(1, 15):
        t = threshold_for_level(level)
        assert t > prev
        prev = t


def test_progress_bounds() -> None:
    level, into, needed = progress(150)
    assert level == 2
    assert into > 0
    assert needed > into
