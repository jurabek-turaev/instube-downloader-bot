# Instube Downloader Bot 🤖🎥

A Telegram bot that **downloads** media from YouTube and Instagram and **converts** media between Telegram's native formats. It's built with `aiogram 3`, `yt-dlp`, `gallery-dl` and `ffmpeg`, and runs next to a **Local Bot API Server**, so it can handle files of **up to 2 GB**. Everything runs in Docker.

## ✨ Features

### 📥 Download

**YouTube:** send a link (video or Shorts) and pick a format:

| Button | Result |
|--------|--------|
| 🎬 Video | mp4, up to 720p (video + audio merged by ffmpeg) |
| 🎧 Audio | mp3, 192 kbps |

**Instagram:** send a link and the bot figures out what it is:

| Link | Result |
|------|--------|
| Reel / video post | 🎥 Video |
| Photo post | 🖼 Photo |
| Carousel (photos, videos or both) | 📚 Album(s) of up to 10 items each, every item sent as the right type |
| Story | 🎥 / 🖼 The story item |

Instagram cookies are supported, so content that needs a logged-in session works too.

### ⚡ Instant re-sends (file_id cache)
After a YouTube video or audio is sent once, the bot saves its Telegram `file_id` in SQLite. The next request for the same link (by anyone) is sent straight from Telegram's servers: no download, no upload, it arrives instantly. Video and audio versions are cached separately.

### 🔄 Convert
Just send a file. No commands or buttons are needed: the bot detects the type and converts it automatically.

| You send | You get |
|----------|---------|
| 🎵 mp3 / audio file | 🎤 Voice message (OGG/OPUS) |
| 🎤 Voice message | 🎵 mp3 file: *the bot asks you to name it, or you can Skip* |
| 🎥 Video (mp4) | ⭕ Round video note (cropped to a centered square) |
| ⭕ Video note | 🎥 Regular video file |

### 👑 Admin
The admin is set by `ADMIN_ID` in `.env`. Other users get no response to these commands.

| Command | What it does |
|---------|--------------|
| `/stats` | Total / active users, joined today, last 7 days, total downloads |
| `/export` | All users as an `.xlsx` file |

Every user who messages the bot is saved to SQLite (`users` table) by a middleware.

### 🛡️ Other
- Clear error messages: the user gets a simple reason, and the full technical error goes to the logs.
- Oversized files are rejected **before** downloading when the size is known, and the real file size is checked again after downloading.
- Temporary files are always cleaned up, even when sending fails. This includes the copies the Local Bot API server keeps of files users send.
- Videos longer than 60s are trimmed for video notes, and the user is told.

## 🛠️ Tech Stack

- **Language:** Python 3.12
- **Framework:** [aiogram 3.x](https://docs.aiogram.dev/), an async Telegram Bot API framework
- **Bot API:** [telegram-bot-api](https://github.com/tdlib/telegram-bot-api) in `--local` mode ([aiogram/telegram-bot-api](https://hub.docker.com/r/aiogram/telegram-bot-api) image)
- **Downloaders:** [yt-dlp](https://github.com/yt-dlp/yt-dlp) (+ [deno](https://deno.com/) for YouTube's JS challenges), [gallery-dl](https://github.com/mikf/gallery-dl) for Instagram photos/carousels/stories
- **Media processing:** [ffmpeg](https://ffmpeg.org/) for format conversion, cropping and stream merging
- **Database:** SQLite (users, media cache)
- **Package manager:** [uv](https://github.com/astral-sh/uv)
- **Deployment:** Docker & Docker Compose

## 📁 Project Structure

```text
instube-downloader-bot/
├── main.py                 # Entry point: middleware, DB init, routers, polling
├── config.py               # Env vars, size limits, bot (local/cloud API) & dispatcher
├── handlers/
│   ├── commands.py         # /start, /stats, /export
│   ├── audio.py            # mp3 → voice, voice → mp3 (with FSM name prompt)
│   ├── video.py            # video → video note, video note → video
│   └── links.py            # YouTube/Instagram links, format buttons, file_id cache
├── middleware/
│   └── user.py             # Saves/updates every user in the DB
├── services/
│   ├── downloader.py       # yt-dlp / gallery-dl logic, cache keys
│   ├── converter.py        # ffmpeg logic
│   ├── database.py         # SQLite: users, stats, media_cache
│   └── export.py           # /export → .xlsx (openpyxl)
├── utils/
│   └── files.py            # Size checks, downloading user files, cleanup
├── docker-compose.yml      # Bot + Local Bot API server
├── Dockerfile
├── pyproject.toml          # Dependencies (uv)
├── uv.lock
├── .gitattributes          # Forces LF line endings
├── .env                    # Secrets: never committed
├── cookies.txt             # Instagram session: never committed
└── bot.db                  # SQLite database: never committed
```

**Router order matters.** In `main.py`, routers are registered specific-first: `commands` → `audio` → `video` → `links`. The `links` router ends with a catch-all `@router.message()`, so it must come last or it would swallow every media message.

## 🏗️ How large files work

The public Bot API (`api.telegram.org`) only lets a bot download user files up to **20 MB** and send files up to **50 MB**. To get past that, `docker-compose.yml` runs Telegram's own Bot API server next to the bot:

```text
Telegram user ⇄ Telegram ⇄ telegram-bot-api (--local) ⇄ instube-bot
                                   │                         │
                                   └── shared volume ────────┘
                                     /var/lib/telegram-bot-api
```

- In `--local` mode the server allows **uploads up to 2000 MB** and **downloads of any size**.
- `getFile` returns a **local path** instead of a URL, so both containers mount the same volume **at the same path**, and the bot reads files straight from disk.
- The bot switches to the local server when `LOCAL_API_URL` is set. Without it, the bot uses the public API and the 20 MB / 50 MB limits.

## 🚀 Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)
- A bot token from [@BotFather](https://t.me/BotFather)
- `api_id` and `api_hash` from [my.telegram.org](https://my.telegram.org) → *API development tools* (required by the Local Bot API server)

### 1. Clone and configure

```bash
git clone https://github.com/jurabek-turaev/instube-downloader-bot.git
cd instube-downloader-bot
```

Create a `.env` file:

```env
BOT_TOKEN=your_telegram_bot_token_here
ADMIN_ID=your_telegram_user_id

# Local Bot API server (my.telegram.org)
TELEGRAM_API_ID=1234567
TELEGRAM_API_HASH=your_api_hash_here
LOCAL_API_URL=http://telegram-bot-api:8081

# Optional
COOKIES_FILE=cookies.txt
DB_PATH=bot.db
```

| Variable | Required | Description |
|----------|----------|-------------|
| `BOT_TOKEN` | ✅ | Bot token from @BotFather |
| `ADMIN_ID` | — | Your Telegram user ID. If it's missing, admin commands are disabled. |
| `TELEGRAM_API_ID`, `TELEGRAM_API_HASH` | ✅ for Docker | Credentials for the Local Bot API server |
| `LOCAL_API_URL` | — | Set it to use the local server (2 GB limits); leave it empty to use the public API |
| `COOKIES_FILE` | — | Path to Instagram cookies (default `cookies.txt`) |
| `DB_PATH` | — | SQLite file (default `bot.db`) |

> ⚠️ Save `.env` with **LF** line endings. A `.env` created on Windows (CRLF) adds an invisible `\r` to every value. Fix it with `sed -i 's/\r$//' .env`.

### 2. Instagram cookies (optional, but recommended)

Instagram blocks anonymous requests, so most posts fail without a logged-in session. To enable them:

1. Use a **throwaway Instagram account**, because automated downloading can get accounts banned.
2. Install the *Get cookies.txt LOCALLY* browser extension.
3. Log in to `instagram.com`, click the extension, and export.
4. Save the file as `cookies.txt` in the project root (Netscape format).

> ⚠️ `cookies.txt` is as sensitive as a password. It's gitignored, so keep it that way.
> Cookies expire after a few weeks. Refresh the file and restart the container; no rebuild is needed.

YouTube works fine without cookies.

### 3. Log the bot out of the public API (once)

Before a bot can work with a local Bot API server, it must be logged out of `api.telegram.org`. Stop the bot first, then:

```bash
curl "https://api.telegram.org/bot$(grep '^BOT_TOKEN=' .env | cut -d= -f2-)/logOut"
```

You should get `{"ok":true,"result":true}`. After this, the bot can't log back in to the public API for 10 minutes. You only do this once per bot.

### 4. Run

```bash
docker compose up -d --build
```

```bash
docker compose logs -f
```

`Run polling for bot @your_bot` in the logs means it's working.

## 💻 Development

The project folder is mounted into the container, so **code changes only need a restart**, not a rebuild:

```bash
docker compose restart instube-bot
```

A rebuild is required when `Dockerfile`, `pyproject.toml` or `uv.lock` changes. Use `-V`: the container keeps `.venv` in an anonymous volume, and without `-V` the **old** dependencies are reused:

```bash
docker compose up -d --build -V
```

### Updating yt-dlp
YouTube changes often. When downloads start failing (for example with `HTTP Error 403`), updating yt-dlp usually fixes it:

```bash
uv lock --upgrade-package yt-dlp
```

```bash
docker compose up -d --build -V
```

### Useful commands

Disk used by the Local Bot API server:

```bash
docker exec telegram-bot-api du -sh /var/lib/telegram-bot-api
```

Cached media:

```bash
docker exec instube-downloader-bot .venv/bin/python -c "import sqlite3; print(sqlite3.connect('bot.db').execute('select * from media_cache').fetchall())"
```

<details>
<summary>Running locally without Docker</summary>

You'll need `ffmpeg` and `deno` installed on your system. Leave `LOCAL_API_URL` empty: the bot will use the public Bot API with the 20 MB / 50 MB limits. Remember that if the bot was logged out (step 3), you need to wait 10 minutes and make sure the Docker version isn't running at the same time.

```bash
uv sync
```

```bash
uv run main.py
```
</details>

## ⚠️ Limitations

- **File limits.** With the Local Bot API server: up to **2000 MB** both ways. Without it: 20 MB for files users send and 50 MB for downloads. Larger files are rejected with a clear message.
- **Speed depends on the host.** The first download of a large video is limited by the server's internet connection (YouTube → bot → Telegram). Repeat requests are instant thanks to the `file_id` cache.
- **The cache is per bot.** A `file_id` only works for the bot that sent it, so a test bot and the production bot each build their own cache.
- **Video notes are capped at 60 seconds** by Telegram. Longer videos are trimmed to the first 60s.
- **Private content.** Private Instagram accounts and age-restricted YouTube videos need valid cookies from an account with access.
- **Playlists aren't supported.** A `watch?v=...&list=...` link downloads just that video.
- **Round video notes recorded by Telegram** have empty corners. Converting them back to a regular video shows white corners, because those pixels were never recorded. Video notes the bot created from a full-frame video convert back with the corners intact.
