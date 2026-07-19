import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()
logger = logging.getLogger(__name__)

@router.message(Command("start"))
async def cmd_start(message: Message):
    telegram_id = message.from_user.id
    fullname = message.from_user.full_name
    username = message.from_user.username

    logger.info("New user: ID=%s, Fullname=%s, Username=%s", telegram_id, fullname, username)
    
    await message.answer(
        "👋 <b>Hi there!</b>\n\n"
        "I download media and convert it between Telegram formats.\n\n"
        "<b>📥 Download</b>\n"
        "Send me a <b>YouTube</b> or <b>Instagram</b> link — you'll choose video or audio.\n\n"
        "<b>🔄 Convert</b>\n"
        "Just send me a file, I'll convert it automatically:\n"
        "• 🎵 <b>mp3</b> → voice message\n"
        "• 🎤 <b>voice</b> → mp3 file (you can name it)\n"
        "• 🎥 <b>video</b> → round video note\n"
        "• ⭕ <b>video note</b> → regular video\n\n"
        "<i>Max file size: 50 MB</i>",
        parse_mode="HTML",
    )
