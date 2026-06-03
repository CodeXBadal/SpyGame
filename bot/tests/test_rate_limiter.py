"""Tests for the in-memory rate limiter."""
import asyncio

import pytest

from bot.middleware.rate_limiter import RateLimiter


@pytest.mark.asyncio
async def test_rate_limit_blocks_after_threshold() -> None:
    limiter = RateLimiter(window=2, max_calls=3)
    allowed = []
    for _ in range(5):
        allowed.append(await limiter.allow("u:1"))
    assert allowed[:3] == [True, True, True]
    assert allowed[3] is False
    assert allowed[4] is False


@pytest.mark.asyncio
async def test_rate_limit_window_resets() -> None:
    limiter = RateLimiter(window=1, max_calls=2)
    assert await limiter.allow("u:1") is True
    assert await limiter.allow("u:1") is True
    assert await limiter.allow("u:1") is False
    await asyncio.sleep(1.2)
    assert await limiter.allow("u:1") is True
