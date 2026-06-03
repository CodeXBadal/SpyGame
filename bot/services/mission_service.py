"""Mission progress, claiming, and seeding."""
from __future__ import annotations

import json
import os
from typing import Dict, List, Optional

from bot.database.repositories import MissionRepository, UserRepository
from bot.models.mission import MissionModel, MissionProgress
from bot.services.reward_service import RewardService
from bot.utils.logger import get_logger
from bot.utils.time_utils import utcnow

log = get_logger(__name__)


def _period_key(period: str) -> str:
    now = utcnow()
    if period == "daily":
        return now.strftime("%Y-%m-%d")
    if period == "weekly":
        iso = now.isocalendar()
        return f"{iso.year}-W{iso.week:02d}"
    return now.strftime("%Y-%m-%d")


class MissionService:
    def __init__(
        self,
        missions: MissionRepository,
        rewards: RewardService,
        data_path: Optional[str] = None,
    ) -> None:
        self._missions = missions
        self._rewards = rewards
        self._data_path = data_path or os.path.join(
            os.path.dirname(__file__), "..", "data", "missions.json"
        )

    async def seed_from_file(self) -> int:
        path = os.path.abspath(self._data_path)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        items = data.get("missions", [])
        for item in items:
            await self._missions.upsert_mission(MissionModel(**item))
        log.info("Seeded %d missions from %s", len(items), path)
        return len(items)

    async def increment_metric(
        self, user_id: int, metric: str, amount: int = 1
    ) -> List[MissionProgress]:
        """Increment all missions matching `metric`. Returns updated progress entries."""
        all_missions = await self._missions.list_missions()
        updated: List[MissionProgress] = []
        for mission in all_missions:
            if mission.metric != metric:
                continue
            period_key = _period_key(mission.period)
            progress = await self._missions.increment_progress(
                user_id, mission, period_key, amount=amount
            )
            updated.append(progress)
        return updated

    async def list_for_user(
        self, user_id: int
    ) -> Dict[str, List[Dict]]:
        """Return missions grouped by period with progress merged."""
        all_missions = await self._missions.list_missions()
        result: Dict[str, List[Dict]] = {"daily": [], "weekly": []}
        for mission in all_missions:
            period_key = _period_key(mission.period)
            progress = await self._missions.get_progress(
                user_id, mission.mission_id, period_key
            )
            entry = {
                "mission": mission,
                "progress": progress.progress if progress else 0,
                "target": mission.target,
                "completed": progress.completed if progress else False,
                "claimed": progress.claimed if progress else False,
            }
            bucket = result.setdefault(mission.period, [])
            bucket.append(entry)
        return result

    async def claim(self, user_id: int, mission_id: str) -> Optional[MissionModel]:
        all_missions = await self._missions.list_missions()
        mission = next((m for m in all_missions if m.mission_id == mission_id), None)
        if not mission:
            return None
        period_key = _period_key(mission.period)
        ok = await self._missions.mark_claimed(user_id, mission_id, period_key)
        if not ok:
            return None
        await self._rewards.grant(
            user_id=user_id,
            xp=mission.reward_xp,
            coins=mission.reward_coins,
            reason=f"mission:{mission_id}",
        )
        return mission
