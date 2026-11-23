import logging
import asyncio
from aiogram import Router, F
from aiogram.types import Message, FSInputFile, KeyboardButton, ReplyKeyboardMarkup
from aiogram.filters import Command, BaseFilter
from config import is_admin, MAX_INCOMING_FILESIZE, MAX_FILESIZE
from services.database import get_stats
from services.export import build_users_xlsx
from utils.files import cleanup, size_text

router = Router()
logger = logging.getLogger(__name__)

BTN_STATS = "📊 Statistics"
BTN_EXPORT = "📥 Export users"

admin_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=BTN_STATS), KeyboardButton(text=BTN_STATS)]],
    resize_keyboard=True,
    is_persistent=True,
)

class IsAdmin(BaseFilter):
    """Let the handler run only for the admin."""
    async def __call__(self, message: Message) -> bool:
        return is_admin(message.from_user.id)

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
        f"<i>Max size: {size_text(MAX_INCOMING_FILESIZE)} for files you send, {size_text(MAX_FILESIZE)} for downloads</i>\n\n"
        "❓ More details: /help",
        parse_mode="HTML",
        reply_markup=admin_keyboard if is_admin(message.from_user.id) else None,
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "❓ <b>How to use the bot</b>\n\n"
        "<b>📥 YouTube</b>\n"
        "Send a video or Shorts link, then pick:\n"
        "• 🎬 <b>Video</b>: mp4, up to 720p\n"
        "• 🎧 <b>Audio</b>: mp3, 192 kbps\n\n"
        "<b>📸 Instagram</b>\n"
        "Send a reel, post, carousel or story link. "
        "Photos and videos are sent automatically, no buttons needed.\n\n"
        "<b>🔄 Converting files</b>\n"
        "Send a file and I'll convert it:\n"
        "• 🎵 mp3 → 🎤 voice message\n"
        "• 🎤 voice → 🎵 mp3 (you can give it a name)\n"
        "• 🎥 video → ⭕ round video note (first 60 seconds)\n"
        "• ⭕ video note → 🎥 regular video\n\n"
        "<b>⚠️ Good to know</b>\n"
        "• Private Instagram accounts can't be downloaded\n"
        "• Playlists aren't supported; send a link to a single video\n"
        f"• Max size: {size_text(MAX_INCOMING_FILESIZE)} for files you send, "
        f"{size_text(MAX_FILESIZE)} for downloads",
        parse_mode="HTML",
    )


@router.message(Command("stats"), IsAdmin())
@router.message(F.text == BTN_STATS, IsAdmin())
async def cmd_stats(message: Message):
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


@router.message(Command("export"), IsAdmin())
@router.message(F.text == BTN_EXPORT, IsAdmin())
async def cmd_export(message: Message):
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
