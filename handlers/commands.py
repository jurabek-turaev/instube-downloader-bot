import logging
import asyncio
from aiogram import Router
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command
from config import is_admin, MAX_INCOMING_FILESIZE, MAX_FILESIZE
from services.database import get_stats
from services.export import build_users_xlsx
from utils.files import cleanup, size_text

router = Router()
logger = logging.getLogger(__name__)

@router.message(Command("start"))
async def cmd_start(message: Message):
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
        f"<i>Max size: {size_text(MAX_INCOMING_FILESIZE)} for files you send, {size_text(MAX_FILESIZE)} for downloads</i>",
        parse_mode="HTML",
    )

@router.message(Command("stats"))
async def cmd_stats(message: Message):
    if not is_admin(message.from_user.id):
        return

    s = await asyncio.to_thread(get_stats)
    await message.answer(
        "📊 <b>Bot statistics</b>\n\n"
        f"👥 Total users: <b>{s['total']}</b>\n"
        f"✅ Active: <b>{s['active']}</b>\n"
        f"🆕 Joined today: <b>{s['today']}</b>\n"
        f"📅 Last 7 days: <b>{s['week']}</b>\n"
        f"⬇️ Total downloads: <b>{s['downloads']}</b>",
        parse_mode="HTML",
    )


@router.message(Command("export"))
async def cmd_export(message: Message):
    if not is_admin(message.from_user.id):
        return

    status = await message.answer("⌛ Building export...")
    path = None
    try:
        path = await asyncio.to_thread(build_users_xlsx)
        await message.answer_document(
            document=FSInputFile(path, filename="users.xlsx"),
            caption="📊 Users export",
        )
    except Exception:
        logger.exception("Export failed")
        await message.answer("❌ Couldn't build the export. Please try again.")
    finally:
        await status.delete()
        cleanup(path)
