# Instube Downloader Bot 🤖🎥

A fast, lightweight, and efficient Telegram bot built with Python that downloads videos directly from YouTube and Instagram. The bot is fully containerized using Docker and utilizes `uv` for blazing-fast dependency management.

## ✨ Features

- **Multi-Platform Support:** Download videos from YouTube and Instagram using just the video URL.
- **Optimized for Telegram:** Automatically selects the best video format under Telegram's 50MB file size limit.
- **No Extra Dependencies:** Downloads merged audio/video (`mp4`) formats directly, removing the need for `ffmpeg`.
- **Fast Package Management:** Uses `uv` instead of standard `pip` for rapid dependency resolution and environment isolation.
- **Fully Containerized:** Easy to deploy anywhere using Docker and Docker Compose.

## 🛠️ Tech Stack

- **Language:** Python 3.12+
- **Framework:** [aiogram 3.x](https://docs.aiogram.dev/) (Asynchronous Telegram Bot API)
- **Downloader:** [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- **Package Manager:** [uv](https://github.com/astral-sh/uv)
- **Deployment:** Docker & Docker Compose

## 🚀 Getting Started

Follow these instructions to get a copy of the project up and running on your local machine or server.

### Prerequisites

You need to have the following installed on your system:
- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)
- A Telegram Bot Token (get it from [@BotFather](https://t.me/BotFather) on Telegram)

### Installation & Setup

**1. Clone the repository**
```bash
git clone [https://github.com/yourusername/instube-downloader-bot.git](https://github.com/yourusername/instube-downloader-bot.git)
cd instube-downloader-bot
```

**2. Configure Environment Variables**
Create a `.env` file in the root directory and add your Telegram Bot Token:
```env
BOT_TOKEN=your_telegram_bot_token_here
```

**3. Run with Docker Compose**
Build and start the bot in detached mode:
```bash
docker compose up -d --build
```

**4. Check Logs (Optional)**
To verify that the bot is running smoothly:
```bash
docker compose logs -f
```

## 💻 Local Development (Without Docker)

If you want to run or test the bot locally without Docker, you can use `uv`:

```bash
# Install dependencies
uv sync

# Run the bot
uv run main.py
```

## ⚠️ Limitations

- **File Size Limit:** By default, the Telegram Bot API restricts bots from uploading files larger than **50 MB**. The bot is configured to handle this safely by stopping the download if the target file exceeds this limit.
- **Private Content:** The bot cannot download videos from private Instagram accounts or age-restricted YouTube videos without passing cookies/authentication.

## 📁 Project Structure

```text
instube-downloader-bot/
├── .env                # Environment variables (ignored in git)
├── .dockerignore       # Files to ignore in Docker build
├── docker-compose.yml  # Docker Compose configuration
├── Dockerfile          # Docker image build instructions
├── main.py             # Main bot application logic
├── pyproject.toml      # Project metadata and dependencies (uv)
├── uv.lock             # Dependency lockfile
└── README.md           # Project documentation
```