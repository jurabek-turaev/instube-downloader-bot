import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
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

VIDEO_NOTE_SIZE = 384
VIDEO_NOTE_MAX_DURATION = 60


MB = 1024 * 1024

LOCAL_API_URL = os.getenv("LOCAL_API_URL")
USE_LOCAL_API = bool(LOCAL_API_URL)

if USE_LOCAL_API:
    # Local Bot API server: no getFile limit, uploads up to 2000MB
    MAX_FILESIZE = 2000 * MB
    MAX_INCOMING_FILESIZE = 2000 * MB
else:
    MAX_FILESIZE = 50 * MB
    MAX_INCOMING_FILESIZE = 20 * MB


session = None
if USE_LOCAL_API:
    session = AiohttpSession(
        api=TelegramAPIServer.from_base(LOCAL_API_URL, is_local=True),
        timeout=900,
    )

bot = Bot(BOT_TOKEN, session=session)
dp = Dispatcher(storage=MemoryStorage())
