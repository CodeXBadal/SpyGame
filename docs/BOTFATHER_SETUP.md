# 🤖 BotFather Setup Guide

This guide creates your Telegram bot and configures it for **group play**.

---

## 1. Create the bot

1. In Telegram, open a chat with **@BotFather**.
2. Send `/newbot`.
3. Choose a **name** (e.g. `My Spy Game`).
4. Choose a **username** ending in `bot` (e.g. `MySpyGameBot`).
5. Save the **API token** — this is your `BOT_TOKEN` for `.env`.

## 2. CRITICAL — Disable Privacy Mode

The bot **must read all group messages** to detect commands. By default BotFather enables Privacy Mode (bot only sees `/commands`, replies, and mentions). Disable it:

```
/setprivacy   →   select your bot   →   Disable
```

> Even if you keep privacy mode ON, all `/commands` still work — but you'll get a more robust experience with privacy disabled.

## 3. Allow the bot to be added to groups

```
/setjoingroups   →   select your bot   →   Enable
```

## 4. Set the command menu

```
/setcommands   →   select your bot
```

Paste this list:

```
start - Welcome message
help - Show all commands
spy - Start a Spy Game lobby
startgame - Start a Spy Game lobby
join - Join the current lobby
leave - Leave the current lobby
forcestart - Force the game to start
cancelgame - Cancel the current game
ask - Ask another player a question
next - Pass the question turn
vote - Open voting for the spy
guess - Spy guesses the location
profile - Show your profile
rank - Show your ranks
leaderboard - Show top players
top - Show top players
achievements - Show your achievements
daily - Claim your daily reward
missions - Show your missions
claim - Claim a completed mission
admin - Open admin panel
setminplayers - Set min players (admin)
setmaxplayers - Set max players (admin)
settimer - Set a phase timer (admin)
setlanguage - Set group language (admin)
forcestop - Force-stop the current game (admin)
```

## 5. Set a description & about text

```
/setdescription   →   "Multiplayer Spy Game for Telegram groups. Identify the spy or guess the location!"
/setabouttext     →   "Spy Game Bot — 🕵️ identify the spy or guess the location!"
/setuserpic       →   upload a 512×512 logo
```

## 6. Add the bot to a group & promote it

1. Open the target group → **Add member** → search your bot username.
2. **Promote the bot to admin** with at least these permissions:
   - Delete messages
   - Pin messages (optional, nice for lobby messages)
3. Send `/spy` in the group to verify it works.

## 7. Save your owner ID

To use owner-only commands like `/broadcast`, you need your numeric Telegram ID.

Message **@userinfobot** in Telegram → it replies with your ID (e.g. `123456789`).

Set in `.env`:
```
OWNER_IDS=123456789
```

(Comma-separate for multiple owners.)
