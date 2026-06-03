"""Core game engine: lobby, roles, questions, voting, results."""
from __future__ import annotations

import asyncio
import random
import uuid
from datetime import timedelta
from typing import Dict, List, Optional, Tuple

from bot.cache.cache_manager import CacheManager
from bot.config import settings
from bot.database.repositories import (
    AuditRepository,
    GameRepository,
    GroupRepository,
    UserRepository,
)
from bot.models.game import (
    GameModel,
    GamePhase,
    GameStatus,
    PlayerModel,
    Role,
    VoteModel,
)
from bot.services.achievement_service import AchievementService
from bot.services.location_service import LocationService
from bot.services.mission_service import MissionService
from bot.services.reward_service import RewardService
from bot.utils.logger import get_logger
from bot.utils.time_utils import utcnow

log = get_logger(__name__)


class GameService:
    """Stateful, async game engine. One game per group at a time."""

    def __init__(
        self,
        games: GameRepository,
        groups: GroupRepository,
        users: UserRepository,
        audit: AuditRepository,
        rewards: RewardService,
        achievements: AchievementService,
        missions: MissionService,
        locations: LocationService,
        cache: CacheManager,
    ) -> None:
        self._games = games
        self._groups = groups
        self._users = users
        self._audit = audit
        self._rewards = rewards
        self._achievements = achievements
        self._missions = missions
        self._locations = locations
        self._cache = cache
        self._locks: Dict[int, asyncio.Lock] = {}

    # ---------- helpers ----------
    def _lock_for(self, group_id: int) -> asyncio.Lock:
        lock = self._locks.get(group_id)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[group_id] = lock
        return lock

    async def get_active(self, group_id: int) -> Optional[GameModel]:
        cache_key = f"game:active:{group_id}"
        cached = await self._cache.get(cache_key)
        if cached is not None:
            return cached
        game = await self._games.get_active_for_group(group_id)
        if game:
            await self._cache.set(cache_key, game, ttl=3600)
        return game

    async def _persist(self, game: GameModel) -> None:
        await self._games.save(game)
        await self._cache.set(f"game:active:{game.group_id}", game, ttl=3600)

    async def _drop_cache(self, group_id: int) -> None:
        await self._cache.delete(f"game:active:{group_id}")

    # ---------- lobby ----------
    async def create_lobby(
        self,
        group_id: int,
        group_title: Optional[str],
        host_id: int,
    ) -> Tuple[Optional[GameModel], Optional[str]]:
        async with self._lock_for(group_id):
            existing = await self.get_active(group_id)
            if existing:
                return None, "A game is already running in this group."
            group = await self._groups.get_or_create(group_id, title=group_title)
            game = GameModel(
                game_id=str(uuid.uuid4()),
                group_id=group_id,
                host_id=host_id,
                min_players=group.min_players,
                max_players=group.max_players,
                phase_deadline=utcnow()
                + timedelta(seconds=group.lobby_countdown),
            )
            await self._persist(game)
            await self._audit.log(
                action="game_created",
                actor_id=host_id,
                group_id=group_id,
                game_id=game.game_id,
            )
            return game, None

    async def join(
        self, group_id: int, user_id: int, username: Optional[str], full_name: str
    ) -> Tuple[Optional[GameModel], Optional[str]]:
        async with self._lock_for(group_id):
            game = await self.get_active(group_id)
            if not game or game.status != GameStatus.LOBBY:
                return None, "No open lobby. Use /startgame first."
            if game.has_player(user_id):
                return game, "You are already in the lobby."
            if game.player_count >= game.max_players:
                return game, "Lobby is full."
            await self._users.get_or_create(
                user_id=user_id, username=username, full_name=full_name
            )
            game.players[str(user_id)] = PlayerModel(
                user_id=user_id, username=username, full_name=full_name
            )
            await self._persist(game)
            return game, None

    async def leave(
        self, group_id: int, user_id: int
    ) -> Tuple[Optional[GameModel], Optional[str]]:
        async with self._lock_for(group_id):
            game = await self.get_active(group_id)
            if not game or game.status != GameStatus.LOBBY:
                return None, "No open lobby."
            if not game.has_player(user_id):
                return game, "You are not in the lobby."
            del game.players[str(user_id)]
            await self._persist(game)
            return game, None

    async def cancel(
        self, group_id: int, actor_id: int, force: bool = False
    ) -> Tuple[bool, Optional[str]]:
        async with self._lock_for(group_id):
            game = await self.get_active(group_id)
            if not game:
                return False, "No active game."
            if (not force) and actor_id != game.host_id:
                return False, "Only the host can cancel this game."
            await self._games.cancel_game(game.game_id)
            await self._drop_cache(group_id)
            await self._audit.log(
                action="game_cancelled",
                actor_id=actor_id,
                group_id=group_id,
                game_id=game.game_id,
            )
            return True, None

    # ---------- start ----------
    async def start_game(
        self, group_id: int, actor_id: int, force: bool = False
    ) -> Tuple[Optional[GameModel], Optional[str]]:
        async with self._lock_for(group_id):
            game = await self.get_active(group_id)
            if not game or game.status != GameStatus.LOBBY:
                return None, "No lobby to start."
            if (not force) and actor_id != game.host_id:
                return None, "Only the host can start the game."
            if game.player_count < game.min_players:
                return (
                    None,
                    f"Need at least {game.min_players} players (currently {game.player_count}).",
                )
            group = await self._groups.get_or_create(group_id)
            location = self._locations.pick(recent=group.recent_locations)
            player_ids = list(game.players.keys())
            spy_key = random.choice(player_ids)
            spy_id = int(spy_key)
            for key, player in game.players.items():
                player.role = Role.SPY if key == spy_key else Role.CIVILIAN
            game.location = location
            game.spy_id = spy_id
            game.status = GameStatus.RUNNING
            game.phase = GamePhase.QUESTION
            game.started_at = utcnow()
            # First asker is random
            game.current_asker_id = int(random.choice(player_ids))
            group_settings = await self._groups.get_or_create(group_id)
            game.phase_deadline = utcnow() + timedelta(
                seconds=group_settings.question_phase_seconds
            )
            await self._persist(game)
            await self._groups.push_recent_location(
                group_id, location, settings.avoid_recent_locations
            )
            await self._audit.log(
                action="game_started",
                actor_id=actor_id,
                group_id=group_id,
                game_id=game.game_id,
                payload={"location": location, "players": game.player_count},
            )
            return game, None

    # ---------- question phase ----------
    async def record_question(
        self, group_id: int, asker_id: int, target_id: int, question: str
    ) -> Tuple[Optional[GameModel], Optional[str]]:
        async with self._lock_for(group_id):
            game = await self.get_active(group_id)
            if not game or game.status != GameStatus.RUNNING:
                return None, "No running game."
            if game.phase != GamePhase.QUESTION:
                return None, "Not in question phase."
            if game.current_asker_id != asker_id:
                return None, "It's not your turn to ask."
            if not game.has_player(target_id) or target_id == asker_id:
                return None, "Invalid target."
            game.question_history.append(
                {
                    "asker_id": asker_id,
                    "target_id": target_id,
                    "question": question[:300],
                    "at": utcnow().isoformat(),
                }
            )
            game.question_count += 1
            # Pass turn to target
            game.current_asker_id = target_id
            await self._persist(game)
            return game, None

    async def next_asker(
        self, group_id: int, actor_id: int
    ) -> Tuple[Optional[GameModel], Optional[str]]:
        async with self._lock_for(group_id):
            game = await self.get_active(group_id)
            if not game or game.status != GameStatus.RUNNING:
                return None, "No running game."
            if game.phase != GamePhase.QUESTION:
                return None, "Not in question phase."
            if game.current_asker_id != actor_id:
                return None, "Only the current asker can pass."
            ids = game.alive_player_ids
            if not ids:
                return None, "No alive players."
            current = game.current_asker_id
            try:
                idx = ids.index(current)
                game.current_asker_id = ids[(idx + 1) % len(ids)]
            except ValueError:
                game.current_asker_id = random.choice(ids)
            await self._persist(game)
            return game, None

    async def advance_to_discussion(self, group_id: int) -> Optional[GameModel]:
        async with self._lock_for(group_id):
            game = await self.get_active(group_id)
            if not game or game.status != GameStatus.RUNNING:
                return None
            if game.phase != GamePhase.QUESTION:
                return None
            group = await self._groups.get_or_create(group_id)
            game.phase = GamePhase.DISCUSSION
            game.phase_deadline = utcnow() + timedelta(
                seconds=group.discussion_phase_seconds
            )
            await self._persist(game)
            return game

    async def advance_to_voting(self, group_id: int) -> Optional[GameModel]:
        async with self._lock_for(group_id):
            game = await self.get_active(group_id)
            if not game or game.status != GameStatus.RUNNING:
                return None
            if game.phase not in (GamePhase.DISCUSSION, GamePhase.QUESTION):
                return None
            group = await self._groups.get_or_create(group_id)
            game.phase = GamePhase.VOTING
            game.phase_deadline = utcnow() + timedelta(
                seconds=group.voting_phase_seconds
            )
            await self._persist(game)
            return game

    # ---------- voting ----------
    async def cast_vote(
        self, group_id: int, voter_id: int, target_id: int
    ) -> Tuple[Optional[GameModel], Optional[str]]:
        async with self._lock_for(group_id):
            game = await self.get_active(group_id)
            if not game or game.status != GameStatus.RUNNING:
                return None, "No running game."
            if game.phase != GamePhase.VOTING:
                return None, "Not in voting phase."
            if not game.has_player(voter_id):
                return None, "You are not in this game."
            if not game.has_player(target_id):
                return None, "Invalid target."
            if str(voter_id) in game.votes:
                return None, "You have already voted."
            game.votes[str(voter_id)] = VoteModel(voter_id=voter_id, target_id=target_id)
            await self._persist(game)
            await self._audit.log(
                action="vote_cast",
                actor_id=voter_id,
                group_id=group_id,
                game_id=game.game_id,
                payload={"target_id": target_id},
            )
            return game, None

    # ---------- guesses & resolution ----------
    async def spy_guess(
        self, group_id: int, user_id: int, guess: str
    ) -> Tuple[Optional[GameModel], Optional[bool], Optional[str]]:
        """
        Returns (game, correct?, error). If correct=True spy wins; False spy loses.
        """
        async with self._lock_for(group_id):
            game = await self.get_active(group_id)
            if not game or game.status != GameStatus.RUNNING:
                return None, None, "No running game."
            if game.spy_id != user_id:
                return None, None, "Only the Spy can guess."
            normalized_guess = guess.strip().lower()
            correct = (game.location or "").strip().lower() == normalized_guess
            await self._audit.log(
                action="spy_guess",
                actor_id=user_id,
                group_id=group_id,
                game_id=game.game_id,
                payload={"guess": guess, "correct": correct},
            )
            if correct:
                await self._finalize_game(game, winner="spy", trigger="spy_guess_correct")
            else:
                await self._finalize_game(
                    game, winner="civilians", trigger="spy_guess_wrong"
                )
            return game, correct, None

    async def resolve_votes(
        self, group_id: int
    ) -> Tuple[Optional[GameModel], Optional[str]]:
        """Tally votes and finalize the game."""
        async with self._lock_for(group_id):
            game = await self.get_active(group_id)
            if not game or game.status != GameStatus.RUNNING:
                return None, "No running game."
            counts: Dict[int, int] = {}
            for v in game.votes.values():
                counts[v.target_id] = counts.get(v.target_id, 0) + 1
            if not counts:
                await self._finalize_game(game, winner="draw", trigger="no_votes")
                return game, None
            top_target, top_count = max(counts.items(), key=lambda kv: kv[1])
            ties = [uid for uid, c in counts.items() if c == top_count]
            if len(ties) > 1:
                await self._finalize_game(game, winner="draw", trigger="vote_tie")
                return game, None
            if top_target == game.spy_id:
                await self._finalize_game(
                    game, winner="civilians", trigger="vote_correct"
                )
            else:
                await self._finalize_game(game, winner="spy", trigger="vote_wrong")
            return game, None

    async def force_finalize_timeout(self, group_id: int) -> Optional[GameModel]:
        async with self._lock_for(group_id):
            game = await self.get_active(group_id)
            if not game or game.status != GameStatus.RUNNING:
                return None
            await self._finalize_game(game, winner="draw", trigger="timeout")
            return game

    async def _finalize_game(
        self, game: GameModel, winner: str, trigger: str
    ) -> None:
        """Apply rewards & stats; persist final game state."""
        game.status = GameStatus.ENDED
        game.phase = GamePhase.RESULT
        game.winner = winner
        game.ended_at = utcnow()
        await self._games.save(game)
        await self._drop_cache(game.group_id)
        await self._audit.log(
            action="game_ended",
            group_id=game.group_id,
            game_id=game.game_id,
            payload={"winner": winner, "trigger": trigger, "location": game.location},
        )

        # Reward computation
        winning_player_ids = set()
        if winner == "spy" and game.spy_id is not None:
            winning_player_ids.add(game.spy_id)
        elif winner == "civilians":
            for p in game.players.values():
                if p.role == Role.CIVILIAN:
                    winning_player_ids.add(p.user_id)

        for player in game.players.values():
            uid = player.user_id
            # Participation
            await self._rewards.grant(
                user_id=uid,
                xp=10,
                coins=5,
                reason="participation",
                group_id=game.group_id,
                game_id=game.game_id,
            )
            await self._users.increment_counters(uid, games_played=1)
            await self._missions.increment_metric(uid, "games_played", 1)

            if uid in winning_player_ids:
                await self._rewards.grant(
                    user_id=uid,
                    xp=50,
                    coins=25,
                    reason="win",
                    group_id=game.group_id,
                    game_id=game.game_id,
                )
                fields = {"wins": 1, "seasonal_wins": 1}
                if player.role == Role.SPY:
                    fields["spy_wins"] = 1
                else:
                    fields["civilian_wins"] = 1
                await self._users.increment_counters(uid, **fields)
                await self._missions.increment_metric(uid, "wins", 1)
                if player.role == Role.SPY:
                    await self._missions.increment_metric(uid, "spy_wins", 1)
            elif winner == "draw":
                await self._users.increment_counters(uid, draws=1)
            else:
                await self._users.increment_counters(uid, losses=1)

            # Correct vote bonus
            vote = game.votes.get(str(uid))
            if vote and game.spy_id is not None and vote.target_id == game.spy_id:
                await self._rewards.grant(
                    user_id=uid,
                    xp=20,
                    coins=10,
                    reason="correct_vote",
                    group_id=game.group_id,
                    game_id=game.game_id,
                )
                await self._users.increment_counters(uid, correct_votes=1)
                await self._missions.increment_metric(uid, "correct_votes", 1)

            # Spy correct guess bonus
            if (
                trigger == "spy_guess_correct"
                and game.spy_id is not None
                and uid == game.spy_id
            ):
                await self._rewards.grant(
                    user_id=uid,
                    xp=100,
                    coins=50,
                    reason="correct_guess",
                    group_id=game.group_id,
                    game_id=game.game_id,
                )
                await self._users.increment_counters(uid, correct_guesses=1)

            # Achievement check
            await self._achievements.check_and_unlock(uid)
