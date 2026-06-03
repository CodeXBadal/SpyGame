# 🕵️ Telegram Spy Game Bot

A **production-ready**, fully-async multiplayer **Spy Game** Telegram bot built with **python-telegram-bot v22+**, **MongoDB (Motor)**, **APScheduler**, and **Pydantic**.
Engineered to scale to **50,000+ users** and **5,000+ groups** with isolated, persistent game state per group.

---

## ✨ Features

- 🧩 Multi-group support — unlimited groups, one active game per group, zero cross-group leaks
- 🎮 Full game loop: lobby → roles → questions → discussion → voting → results → rewards
- 🕵️ Spy vs Civilians roles delivered privately via DM
- 🌍 **304 built-in locations** with smart "avoid recently used" selection
- 🏆 XP, levels (unlimited scaling), coins, achievements, daily streaks, missions, seasons
- 📊 Global, seasonal & group leaderboards
- 🛠️ Per-group admin panel (min/max players, timers, language)
- 👑 Owner-only commands (broadcast, stats, counts)
- 🛡️ Rate-limiting, abuse detection, anti double-vote, persistent cooldowns
- 💾 Auto-recovery of in-flight games after restart
- ⏰ APScheduler background tasks (cache GC, season rollover, stale game cleanup, stats)
- 🧾 Full audit log of every game action and reward
- 🧱 Clean architecture: Repository + Service Layer + DI Container
- ✅ Type hints everywhere, structured logging with rotation, unit tests

---

## 📁 Project Structure

```
spygame_bot/
├── bot/
│   ├── main.py                  # Application entry point
│   ├── config.py                # Pydantic settings loaded from .env
│   ├── database/
│   │   ├── mongodb.py           # Motor async client
│   │   ├── indexes.py           # Index creation
│   │   └── repositories/        # Repository pattern
│   ├── handlers/                # Telegram command + callback handlers
│   ├── games/                   # Game engine (GameService)
│   ├── services/                # XP, rewards, missions, achievements, etc.
│   ├── cache/                   # In-memory TTL cache
│   ├── middleware/              # Rate limiter
│   ├── models/                  # Pydantic domain models
│   ├── scheduler/               # APScheduler jobs
│   ├── keyboards/               # InlineKeyboard builders
│   ├── data/                    # locations.json, achievements.json, missions.json
│   ├── logs/                    # Rotating log files
│   ├── utils/                   # Logger, text helpers, time helpers
│   └── tests/                   # Pytest suite
├── docs/                        # Deployment & setup guides
├── requirements.txt
├── .env.example
├── pytest.ini
└── README.md
```

---

## 🗄️ MongoDB Schema

| Collection           | Purpose                                                    | Key Indexes                                              |
|----------------------|------------------------------------------------------------|----------------------------------------------------------|
| `users`              | User profile, XP, coins, stats, achievements, daily streak | `user_id` (unique), `xp ↓`, `wins ↓`, `seasonal_xp ↓`    |
| `groups`             | Per-group settings + recent locations + games_played       | `group_id` (unique)                                      |
| `games`              | Game state (status, phase, players, votes, location, spy)  | `game_id` (unique), `group_id`, `status`                 |
| `votes`              | Reserved for analytics / cross-checks                      | `(game_id, voter_id)` unique                             |
| `economy`            | XP/Coin reward ledger                                      | `user_id`, `created_at ↓`                                |
| `missions`           | Mission definitions (daily / weekly)                       | `mission_id` (unique)                                    |
| `mission_progress`   | Per-user mission progress per period                       | `(user_id, mission_id, period_key)` unique               |
| `seasons`            | Monthly seasons                                            | `season_id` (unique), `active`                           |
| `audit_logs`         | Audit trail (game create/end, votes, guesses, rewards…)    | `created_at ↓`, `action`, `group_id`                     |
| `achievements`       | Reserved for future custom achievements                    | `code` (unique)                                          |
| `daily_rewards`      | Reserved (claim ledger if desired)                         | `user_id` (unique)                                       |
| `cooldowns`          | TTL-backed cooldowns                                       | `(user_id, key)` unique, `expires_at` TTL                |

---

## 🎯 Commands

### 🎮 Game (in groups)
`/spy` `/startgame` `/join` `/leave` `/forcestart` `/cancelgame`
`/ask @user question` `/next` `/vote` `/guess LOCATION`

### 👤 Profile / Stats
`/profile` `/rank` `/leaderboard` `/top` `/achievements`

### 💰 Economy
`/daily` `/missions` `/claim <mission_id>`

### 🛠️ Admin (group admins)
`/admin` `/setminplayers` `/setmaxplayers` `/settimer <phase> <sec>`
`/setlanguage <code>` `/forcestop`

### 👑 Owner only
`/broadcast` `/usercount` `/groupcount` `/gamecount` `/stats`

### 📖 General
`/start` `/help` `/ping`

---

## 🏗️ XP & Reward Table

| Event             | XP   | Coins |
|-------------------|------|-------|
| Participation     | +10  | +5    |
| Win               | +50  | +25   |
| Correct vote      | +20  | +10   |
| Correct spy guess | +100 | +50   |

Levels: `L1=0`, `L2=100`, `L3=250`, `L4=500`, then each next level requires **+50%** of the previous step (unlimited scaling).

---

## 🚀 Quick Start (Local)

```bash
git clone <your-repo>
cd spygame_bot
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your BOT_TOKEN, OWNER_IDS, MONGO_URI
python -m bot.main
```

### Run tests
```bash
pytest -q
```

---

## 📦 Deployment

See the `docs/` folder for full step-by-step guides:

- 🐧 [Ubuntu VPS Setup](docs/UBUNTU_SETUP.md)
- 🗄️ [MongoDB Setup](docs/MONGODB_SETUP.md)
- 🤖 [BotFather Setup](docs/BOTFATHER_SETUP.md)
- 🚢 [VPS Deployment](docs/VPS_DEPLOYMENT.md)
- 🔄 [PM2 Setup](docs/PM2_SETUP.md)
- ⚙️ [Systemd Setup](docs/SYSTEMD_SETUP.md)

---

## 🧠 Architecture Notes

- **Repository Pattern** — every Mongo collection has a dedicated repo with type-safe methods, hiding raw Mongo calls from services.
- **Service Layer** — `GameService`, `RewardService`, `AchievementService`, etc. orchestrate business logic and are wired by `ServiceContainer` (DI).
- **One Lock Per Group** — `asyncio.Lock` keyed by `group_id` prevents race conditions on lobby/voting actions.
- **Cache** — async in-memory TTL cache for active games, with MongoDB as source of truth + recovery on restart.
- **Anti-Cheat** — sliding-window rate limiter, persistent cooldown collection with TTL index, per-game vote uniqueness enforced by repository.
- **Background Jobs** — APScheduler runs cache GC, rate-limiter cleanup, stale-game cleanup, monthly season rollover, hourly stats.

---

## 🪪 License

MIT — do whatever you want, just don't blame me 🕵️
