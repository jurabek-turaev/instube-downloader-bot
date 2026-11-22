import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

BOT_TOKEN = os.getenv("BOT_TOKEN")
COOKIES_FILE = os.getenv("COOKIES_FILE", "cookies.txt")
DB_PATH = os.getenv("DB_PATH", "bot.db")
_admin_id = os.getenv("ADMIN_ID", "").strip()
ADMIN_ID = int(_admin_id) if _admin_id.isdigit() else None
if ADMIN_ID is None:
    logging.warning("ADMIN_ID is not set or invalid — admin commands are disabled.")


def is_admin(telegram_id: int) -> bool:
    return ADMIN_ID is not None and telegram_id == ADMIN_ID


DOWNLOADS_DIR = "downloads"
# Bot API limit for files the bot uploads (sendVideo, sendAudio, ...).
MAX_FILESIZE = 50 * 1024 * 1024
# Bot API limit for files the bot downloads from users (getFile).
MAX_INCOMING_FILESIZE = 20 * 1024 * 1024

VIDEO_NOTE_SIZE = 384
VIDEO_NOTE_MAX_DURATION = 60



bot = Bot(BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
