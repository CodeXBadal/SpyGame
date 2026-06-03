# 🟧 PM2 Setup Guide

PM2 is a Node-based process manager — simple to use and great for keeping the bot alive.

---

## 1. Install Node.js + PM2

```bash
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt install -y nodejs
sudo npm install -g pm2
pm2 --version
```

## 2. Create an ecosystem file

```bash
cd ~/spygame_bot
cat > ecosystem.config.js <<'EOF'
module.exports = {
  apps: [
    {
      name: "spygame-bot",
      cwd: "/home/spybot/spygame_bot",
      script: "/home/spybot/spygame_bot/.venv/bin/python",
      args: "-m bot.main",
      interpreter: "none",
      env: {
        PYTHONUNBUFFERED: "1"
      },
      autorestart: true,
      max_restarts: 20,
      restart_delay: 4000,
      max_memory_restart: "500M",
      out_file: "/home/spybot/spygame_bot/bot/logs/pm2-out.log",
      error_file: "/home/spybot/spygame_bot/bot/logs/pm2-err.log",
      merge_logs: true,
      time: true
    }
  ]
};
EOF
```

> Adjust `cwd` and paths if your user/dir differ.

## 3. Start under PM2

```bash
pm2 start ecosystem.config.js
pm2 status
pm2 logs spygame-bot --lines 100
```

## 4. Persist across reboots

```bash
pm2 save
pm2 startup systemd -u spybot --hp /home/spybot
# It prints a `sudo env PATH=...` command — copy and run it.
```

## 5. Day-to-day commands

```bash
pm2 status                  # process list
pm2 logs spygame-bot        # live logs
pm2 restart spygame-bot     # restart after pulling new code
pm2 stop spygame-bot
pm2 delete spygame-bot
pm2 reload spygame-bot      # zero-downtime reload (for stateless workers)
pm2 monit                   # interactive monitor
```

## 6. Updating the bot

```bash
cd ~/spygame_bot
git pull
source .venv/bin/activate
pip install -r requirements.txt
pm2 restart spygame-bot
```
