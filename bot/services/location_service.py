"""Random location selection avoiding recently used locations."""
from __future__ import annotations

import json
import os
import random
from typing import List, Optional, Set

from bot.config import settings
from bot.utils.logger import get_logger

log = get_logger(__name__)


class LocationService:
    """Loads locations from JSON and selects a fresh one per group."""

    def __init__(self, data_path: Optional[str] = None) -> None:
        self._data_path = data_path or os.path.join(
            os.path.dirname(__file__), "..", "data", "locations.json"
        )
        self._locations: List[str] = []
        self._load()

    def _load(self) -> None:
        path = os.path.abspath(self._data_path)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self._locations = list(dict.fromkeys(data.get("locations", [])))
        if not self._locations:
            raise RuntimeError("No locations loaded from JSON file.")
        log.info("Loaded %d locations from %s", len(self._locations), path)

    def all(self) -> List[str]:
        return list(self._locations)

    def pick(self, recent: Optional[List[str]] = None) -> str:
        """Pick a random location not present in `recent` if possible."""
        recent_set: Set[str] = set(recent or [])
        candidates = [loc for loc in self._locations if loc not in recent_set]
        if not candidates:
            # All locations recently used; pick fully at random
            candidates = list(self._locations)
        return random.choice(candidates)
