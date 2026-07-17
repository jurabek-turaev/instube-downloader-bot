# Instube Downloader Bot 🤖🎥

A Telegram bot that **downloads** videos from YouTube and Instagram, and **converts** media between Telegram's native formats. Built with `aiogram 3`, `yt-dlp` and `ffmpeg`, fully containerized with Docker.

## ✨ Features

### 📥 Download
Send a **YouTube** or **Instagram** link and pick a format:

| Button | Result |
|--------|--------|
| 🎬 Video | mp4, up to 720p (video + audio merged by ffmpeg) |
| 🎧 Audio | mp3, 192 kbps |

Instagram cookies are supported, so posts that require a logged-in session work too.

### 🔄 Convert
Just send a file — no commands, no buttons. The bot detects the type and converts it automatically:

| You send | You get |
|----------|---------|
| 🎵 mp3 / audio file | 🎤 Voice message (OGG/OPUS) |
| 🎤 Voice message | 🎵 mp3 file — *the bot asks you to name it, or Skip* |
| 🎥 Video (mp4) | ⭕ Round video note (cropped to a centered square) |
| ⭕ Video note | 🎥 Regular video file |

### 🛡️ Other
- Clear error messages — the user gets a simple reason, full technical errors go to the logs.
- Oversized files are rejected **before** downloading, not after.
- Temporary files are always cleaned up, even when sending fails.
- Videos longer than 60s are trimmed for video notes, and the user is told.

## 🛠️ Tech Stack

- **Language:** Python 3.12+
- **Framework:** [aiogram 3.x](https://docs.aiogram.dev/) — async Telegram Bot API
- **Downloader:** [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- **Media processing:** [ffmpeg](https://ffmpeg.org/) — format conversion, cropping, stream merging
- **Package manager:** [uv](https://github.com/astral-sh/uv)
- **Deployment:** Docker & Docker Compose

## 📁 Project Structure

```text
instube-downloader-bot/
├── main.py                 # Entry point — registers routers, starts polling
├── config.py               # Env vars, constants, bot & dispatcher instances
├── handlers/
│   ├── commands.py         # /start
│   ├── audio.py            # mp3 → voice, voice → mp3 (with FSM name prompt)
│   ├── video.py            # video → video note, video note → video
│   └── links.py            # YouTube/Instagram links + format buttons
├── services/
│   ├── downloader.py       # yt-dlp logic
│   └── converter.py        # ffmpeg logic
├── utils/
│   └── files.py            # Size checks, temp file cleanup
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml          # Dependencies (uv)
├── uv.lock
├── .env                    # Secrets — never committed
└── cookies.txt             # Instagram session — never committed
```

**Router order matters.** In `main.py`, routers are registered specific-first: `commands` → `audio` → `video` → `links`. The `links` router ends with a catch-all `@router.message()`, so it must come last or it would swallow every media message.

## 🚀 Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)
- A bot token from [@BotFather](https://t.me/BotFather)

### 1. Clone and configure

```bash
git clone https://github.com/yourusername/instube-downloader-bot.git
cd instube-downloader-bot
```

Create a `.env` file:

```env
BOT_TOKEN=your_telegram_bot_token_here
COOKIES_FILE=cookies.txt
```

### 2. Instagram cookies (optional, but recommended)

Instagram blocks anonymous requests, so most posts fail without a logged-in session. To enable them:

1. Use a **throwaway Instagram account** — automated downloading can get accounts banned.
2. Install the *Get cookies.txt LOCALLY* browser extension.
3. Log in to `instagram.com`, click the extension, and export.
4. Save the file as `cookies.txt` in the project root (Netscape format).

> ⚠️ `cookies.txt` is as sensitive as a password. It's gitignored — keep it that way.
> Cookies expire after a few weeks; refresh the file and restart the container. No rebuild needed.

YouTube works fine without cookies.

### 3. Run

```bash
docker compose up -d --build
docker compose logs -f
```

## 💻 Development

The whole project is mounted as a volume, so **code changes only need a restart** — no rebuild:

```bash
docker compose restart
```

A rebuild is only required when `Dockerfile` or `pyproject.toml` changes:

```bash
docker compose up -d --build
```

<details>
<summary>Running locally without Docker</summary>

You'll need `ffmpeg` installed on your system.

```bash
uv sync
uv run main.py
```
</details>

## ⚠️ Limitations

- **50 MB file limit.** The Telegram Bot API caps bot uploads at 50 MB. Larger files are rejected with a clear message. Raising this to 2 GB requires running a [Local Bot API Server](https://github.com/tdlib/telegram-bot-api) — planned, not implemented yet.
- **Video notes are capped at 60 seconds** by Telegram. Longer videos are trimmed to the first 60s.
- **Private content.** Private Instagram accounts and age-restricted YouTube videos need valid cookies from an account with access.
- **Round video notes recorded by Telegram** have empty corners. Converting them back to a regular video shows white corners — the pixels were never recorded. Video notes the bot created from a full-frame video convert back with the corners intact.
