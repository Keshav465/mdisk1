# 🎬 SDWB2 Premium Movie Bot

A professional Telegram Movie Bot with **streaming**, **admin dashboard**, **TMDb integration**, and **auto-notifications**.

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/keshav6606/SDWB2)

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔍 **Smart Search** | Fuzzy matching with "Latest First" sorting |
| 🎬 **TMDb Integration** | Auto-fetch movie posters, ratings & plot |
| 🎥 **Web Streaming** | Watch movies in browser or launch in VLC/MX Player |
| 📊 **Admin Dashboard** | Manage users, groups & broadcast at `/dashboard` |
| 🔔 **Auto-Notify** | DMs all users when a new movie is added |
| 🔗 **Link Shortener** | Monetize search result links |
| 🕐 **Auto Delete** | Cleans up search results automatically |
| 🏆 **Premium Groups** | Subscription-based group access |

---

## 🚀 Quick Setup

### Step 1 — Get a TMDb API Key (Free)
1. Go to [https://www.themoviedb.org/settings/api](https://www.themoviedb.org/settings/api)
2. Create a free account and generate an API key
3. Add it as `TMDB_API_KEY` in your environment variables

### Step 2 — Generate Session String
```bash
pip install pyrogram tgcrypto
python -c "from pyrogram import Client; Client('u', api_id=YOUR_ID, api_hash='YOUR_HASH').run()"
```
Copy the session string and add it as `SESSION_STRING`.

### Step 3 — Set Environment Variables

| Variable | Required | Description |
|---|---|---|
| `BOT_TOKEN` | ✅ | From [@BotFather](https://t.me/BotFather) |
| `API_ID` | ✅ | From [my.telegram.org](https://my.telegram.org) |
| `API_HASH` | ✅ | From [my.telegram.org](https://my.telegram.org) |
| `SESSION_STRING` | ✅ | Pyrogram user session |
| `OWNER_ID` | ✅ | Your Telegram user ID |
| `DATABASE_URL` | ✅ | MongoDB URI from [mongodb.com](https://mongodb.com) |
| `DATABASE_CHANNEL` | ✅ | Channel ID(s) for file storage |
| `LOG_CHANNEL` | ✅ | Channel ID for bot logs |
| `URL` | ✅ | Your public deployment URL |
| `ADMIN_PASSWORD` | ✅ | Password for `/dashboard` |
| `BOT_USERNAME` | ✅ | Bot username without @ |
| `TMDB_API_KEY` | ⬜ | For movie posters & ratings |
| `SHORTENER_API` | ⬜ | Monetize links |
| `SHORTENER_SITE` | ⬜ | Your shortener domain |
| `AUTO_DELETE` | ⬜ | `True` or `False` |
| `AUTO_DELETE_TIME` | ⬜ | Seconds (default: 300) |

### Step 4 — Deploy on Render

1. Fork this repository
2. Go to [render.com](https://render.com) → New Web Service
3. Connect your fork
4. Set **Build Command**: `pip install -r requirements.txt`
5. Set **Start Command**: `python3 -m bot`
6. Add all environment variables from the table above
7. Click **Deploy**

---

## 📖 Bot Commands

```
/start      — Start the bot
/help       — Get help
/about      — About this bot
/index      — Set indexed channel (group admins)
/auto_delete — Toggle auto-delete (group admins)
/set_auto_delete — Set auto-delete time (group admins)
/set_api    — Set shortener API (group admins)
/api        — View current shortener API
/remove_api — Remove shortener API
/info       — View group subscription info
/request    — Request subscription from owner
/fsub       — Check force-sub status
```

## 🌐 Web Portal

Once deployed, visit:
- `https://your-url.com/` → Bot status
- `https://your-url.com/dashboard` → Admin Dashboard
- `https://your-url.com/w/{token}` → Secure Movie player

---

Made with ❤️ by [@sdmoviespointes](https://t.me/sdmoviespointes)
