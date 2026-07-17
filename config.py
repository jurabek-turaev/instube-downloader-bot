import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

BOT_TOKEN = os.getenv("BOT_TOKEN")
COOKIES_FILE = os.getenv("COOKIES_FILE", "cookies.txt")

DOWNLOADS_DIR = "downloads"
MAX_FILESIZE = 52428800

VIDEO_NOTE_SIZE = 384
VIDEO_NOTE_MAX_DURATION = 60



bot = Bot(BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
