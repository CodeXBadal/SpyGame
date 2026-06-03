"""XP / level computation."""
from __future__ import annotations

from typing import Tuple


# Level thresholds: spec gives 0, 100, 250, 500 for L1..L4.
# Beyond L4 we extend with a smooth scaling curve.
_BASE_THRESHOLDS = [0, 100, 250, 500]


def level_for_xp(xp: int) -> int:
    """Return the level achieved at given XP. Unlimited scaling."""
    if xp < _BASE_THRESHOLDS[1]:
        return 1
    if xp < _BASE_THRESHOLDS[2]:
        return 2
    if xp < _BASE_THRESHOLDS[3]:
        return 3

    # From level 4 onward: each subsequent level requires +50% over the previous threshold.
    level = 4
    threshold = _BASE_THRESHOLDS[3]
    step = _BASE_THRESHOLDS[3] - _BASE_THRESHOLDS[2]  # 250
    while True:
        next_step = int(step * 1.5)
        next_threshold = threshold + next_step
        if xp < next_threshold:
            return level
        level += 1
        threshold = next_threshold
        step = next_step
        # Safety guard for absurdly large XP
        if level > 10_000:
            return level


def threshold_for_level(level: int) -> int:
    """Return the XP threshold to reach a given level."""
    if level <= 1:
        return 0
    if level - 1 < len(_BASE_THRESHOLDS):
        return _BASE_THRESHOLDS[level - 1]
    threshold = _BASE_THRESHOLDS[3]
    step = _BASE_THRESHOLDS[3] - _BASE_THRESHOLDS[2]
    current_level = 4
    while current_level <= level:
        if current_level == 4:
            current_level += 1
            continue
        step = int(step * 1.5)
        threshold = threshold + step
        current_level += 1
    return threshold


def progress(xp: int) -> Tuple[int, int, int]:
    """Return (current_level, xp_into_level, xp_needed_for_next)."""
    level = level_for_xp(xp)
    current_threshold = threshold_for_level(level)
    next_threshold = threshold_for_level(level + 1)
    xp_into = xp - current_threshold
    xp_needed = next_threshold - current_threshold
    return level, xp_into, xp_needed
