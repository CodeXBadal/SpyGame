# 🗄️ MongoDB Setup Guide (Ubuntu 22.04 / 24.04)

The bot uses MongoDB via the Motor async driver. You can use either self-hosted MongoDB or MongoDB Atlas.

---

## Option A — Self-hosted MongoDB on Ubuntu

### 1. Import MongoDB GPG key

```bash
curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor
```

### 2. Add MongoDB repo

For Ubuntu 22.04 (jammy):
```bash
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
```

For Ubuntu 24.04 (noble):
```bash
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu noble/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
```

### 3. Install & start

```bash
sudo apt update
sudo apt install -y mongodb-org
sudo systemctl enable --now mongod
sudo systemctl status mongod
```

### 4. Create database user (recommended)

```bash
mongosh
```

Inside the shell:
```javascript
use admin
db.createUser({
  user: "spybot",
  pwd:  "CHANGE_THIS_STRONG_PASSWORD",
  roles: [ { role: "readWrite", db: "spygame_bot" } ]
})
exit
```

Enable auth — edit `/etc/mongod.conf`:
```yaml
security:
  authorization: enabled
```

Restart:
```bash
sudo systemctl restart mongod
```

Your URI becomes:
```
mongodb://spybot:CHANGE_THIS_STRONG_PASSWORD@127.0.0.1:27017/spygame_bot?authSource=admin
```

Put it in `.env` as `MONGO_URI`.

### 5. (Optional) Bind to localhost only

In `/etc/mongod.conf`:
```yaml
net:
  port: 27017
  bindIp: 127.0.0.1
```

---

## Option B — MongoDB Atlas (cloud, free tier)

1. Sign up at https://www.mongodb.com/cloud/atlas
2. Create a free M0 cluster
3. Database Access → Add user `spybot` with `Atlas admin` or `readWrite`
4. Network Access → Add your VPS IP (or `0.0.0.0/0` for testing only)
5. Copy the **connection string**, e.g.:
   ```
   mongodb+srv://spybot:<password>@cluster0.abcde.mongodb.net/spygame_bot?retryWrites=true&w=majority
   ```
6. Paste it as `MONGO_URI` in your `.env`.

---

## Index creation

You **don't** need to create indexes manually — the bot creates them automatically on startup via `bot/database/indexes.py`.

## Backups

For self-hosted:
```bash
mongodump --uri="mongodb://spybot:PASS@127.0.0.1:27017/spygame_bot?authSource=admin" --out=/var/backups/spybot-$(date +%F)
```

Schedule weekly with cron:
```bash
sudo crontab -e
# At 03:00 every Sunday
0 3 * * 0 mongodump --uri="..." --out=/var/backups/spybot-$(date +\%F)
```
