# ⚙️ Systemd Setup Guide

Systemd is the **recommended** production setup — it starts on boot, restarts on crash, and integrates with journal logging.

---

## 1. Create the service unit

```bash
sudo nano /etc/systemd/system/spygame-bot.service
```

Paste the following — adjust `User`, `Group`, and paths if your setup differs:

```ini
[Unit]
Description=Telegram Spy Game Bot
After=network-online.target mongod.service
Wants=network-online.target

[Service]
Type=simple
User=spybot
Group=spybot
WorkingDirectory=/home/spybot/spygame_bot

# Load environment from the .env file
EnvironmentFile=/home/spybot/spygame_bot/.env

# Execute the bot using the venv interpreter
ExecStart=/home/spybot/spygame_bot/.venv/bin/python -m bot.main

# Restart policy
Restart=always
RestartSec=5
StartLimitIntervalSec=600
StartLimitBurst=10

# Sane resource limits
LimitNOFILE=65535

# Journal output
StandardOutput=journal
StandardError=journal
SyslogIdentifier=spygame-bot

# Hardening (safe defaults)
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ProtectHome=read-only
ReadWritePaths=/home/spybot/spygame_bot/bot/logs

[Install]
WantedBy=multi-user.target
```

> Note: `EnvironmentFile` reads `KEY=VALUE` lines from `.env`. Avoid quoting values and avoid spaces around `=`. Your existing `.env.example` is already compatible.

## 2. Enable & start

```bash
sudo systemctl daemon-reload
sudo systemctl enable spygame-bot
sudo systemctl start spygame-bot
sudo systemctl status spygame-bot
```

You should see `active (running)`.

## 3. View logs

Live tail (journal):
```bash
sudo journalctl -u spygame-bot -f
```

Filter today's logs:
```bash
sudo journalctl -u spygame-bot --since today
```

Search for errors:
```bash
sudo journalctl -u spygame-bot -p err
```

App-level rotating logs are still written to:
```
/home/spybot/spygame_bot/bot/logs/bot.log
/home/spybot/spygame_bot/bot/logs/error.log
```

## 4. Common operations

```bash
sudo systemctl restart spygame-bot     # after `git pull`
sudo systemctl stop spygame-bot
sudo systemctl reload-or-restart spygame-bot
sudo systemctl disable spygame-bot     # stop running on boot
```

## 5. Update workflow

```bash
sudo su - spybot
cd ~/spygame_bot
git pull
source .venv/bin/activate
pip install -r requirements.txt
exit
sudo systemctl restart spygame-bot
```

The bot restores active lobbies and games from MongoDB automatically on every restart.

## 6. Troubleshooting

| Symptom                           | Fix                                                                         |
|----------------------------------|------------------------------------------------------------------------------|
| `Failed to start ... no such file`| Check `ExecStart` path matches your venv (`which python` inside the venv).   |
| `BOT_TOKEN missing`               | Ensure `.env` exists at `EnvironmentFile` path and is readable by `spybot`.  |
| Repeated restart loop             | `journalctl -u spygame-bot -n 200` to see error, often MongoDB unreachable.  |
| Permission denied on logs         | `chown -R spybot:spybot ~/spygame_bot/bot/logs`                              |
