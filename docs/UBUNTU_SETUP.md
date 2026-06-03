# 🐧 Ubuntu 22.04 / 24.04 Setup Guide

This guide prepares a fresh Ubuntu VPS for running the Spy Game Bot.

---

## 1. Update the system

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget git build-essential ca-certificates gnupg lsb-release ufw software-properties-common
```

## 2. Install Python 3.12

Ubuntu 24.04 already includes 3.12. For Ubuntu 22.04:

```bash
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3.12-dev
```

Verify:

```bash
python3.12 --version    # Python 3.12.x
```

## 3. Create a dedicated user

```bash
sudo adduser --disabled-password --gecos "" spybot
sudo usermod -aG sudo spybot
sudo su - spybot
```

## 4. Clone & install the bot

```bash
cd ~
git clone https://github.com/<you>/spygame_bot.git
cd spygame_bot

python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

cp .env.example .env
nano .env       # fill BOT_TOKEN, OWNER_IDS, MONGO_URI
```

## 5. Configure firewall

```bash
sudo ufw allow OpenSSH
sudo ufw enable
sudo ufw status
```

(No inbound bot ports are needed — the bot uses outbound long-polling.)

## 6. Time sync

```bash
sudo timedatectl set-timezone UTC
sudo systemctl enable --now systemd-timesyncd
```

## 7. Smoke test

```bash
source .venv/bin/activate
python -m bot.main
```

You should see:
```
INFO | MongoDB connected. Database=spygame_bot
INFO | ✅ Bot is running. Press Ctrl+C to stop.
```

Press `Ctrl+C`, then move on to one of the deployment guides:
- [PM2_SETUP.md](PM2_SETUP.md)
- [SYSTEMD_SETUP.md](SYSTEMD_SETUP.md)
