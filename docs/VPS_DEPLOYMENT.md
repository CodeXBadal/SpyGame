# 🚢 VPS Deployment Guide

End-to-end deployment of the Spy Game Bot to a production VPS.

---

## Prerequisites

- ✅ Ubuntu 22.04 / 24.04 VPS (1 vCPU / 1 GB RAM is enough for small-medium load; 2 vCPU / 2 GB recommended for >1k groups)
- ✅ SSH access with sudo
- ✅ A bot token from [@BotFather](BOTFATHER_SETUP.md)
- ✅ MongoDB running ([MONGODB_SETUP.md](MONGODB_SETUP.md))
- ✅ Ubuntu prerequisites installed ([UBUNTU_SETUP.md](UBUNTU_SETUP.md))

---

## 1. Clone & install

```bash
sudo su - spybot
cd ~
git clone https://github.com/<you>/spygame_bot.git
cd spygame_bot

python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 2. Configure environment

```bash
cp .env.example .env
nano .env
```

Required:
- `BOT_TOKEN` — from BotFather
- `OWNER_IDS` — your Telegram user IDs (comma-separated)
- `MONGO_URI` — connection string

## 3. Test run

```bash
source .venv/bin/activate
python -m bot.main
```

You should see `✅ Bot is running.` — then send `/start` to your bot in DM.
Press `Ctrl+C` to stop.

## 4. Run as a service

Pick **one** of:

- 🟦 [Systemd](SYSTEMD_SETUP.md) — recommended for production (auto-start on boot, journal logs)
- 🟧 [PM2](PM2_SETUP.md) — simple process manager, great for developers

## 5. Log monitoring

The bot rotates log files to `bot/logs/`:

```bash
tail -f bot/logs/bot.log         # general
tail -f bot/logs/error.log       # errors only
```

Add an alias for convenience:
```bash
echo "alias spylog='tail -f ~/spygame_bot/bot/logs/bot.log'" >> ~/.bashrc
```

## 6. Updating the bot

```bash
cd ~/spygame_bot
git pull
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart spygame-bot      # if using systemd
# OR
pm2 restart spygame-bot                 # if using PM2
```

The bot **automatically recovers** any in-flight lobbies and running games from MongoDB on startup — no manual intervention required.

## 7. Scaling tips for 50k+ users / 5k+ groups

- Use **MongoDB Atlas** M10+ or a self-hosted replica set for HA.
- Bump `MONGO_MAX_POOL=200` and `concurrent_updates=True` (already on).
- Watch `bot/logs/bot.log` hourly `Stats:` line for trend.
- Run **only one bot process per bot token** (Telegram allows only one long-poll listener per token).
- Move logs to an external service (Loki, Datadog) once you exceed 100MB/day.

## 8. Health check

Owner commands:
```
/stats
/usercount
/groupcount
/gamecount
```

Cron-driven external check (optional):
```bash
sudo crontab -e
*/5 * * * * curl -s "https://api.telegram.org/bot$TOKEN/getMe" >/dev/null || systemctl restart spygame-bot
```
