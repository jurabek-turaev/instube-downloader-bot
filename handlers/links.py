import asyncio
import logging

import yt_dlp
from aiogram import F, Router
from aiogram.types import (
    CallbackQuery, FSInputFile, InlineKeyboardButton,
    InlineKeyboardMarkup, Message,
)

from services.downloader import download_video
from utils.files import cleanup

logger = logging.getLogger(__name__)
router = Router()

SUPPORTED_DOMAINS = ("youtube.com", "youtu.be", "instagram.com")


@router.callback_query(F.data.startswith("dl:"))
async def handle_download(callback: CallbackQuery):
    media_type = callback.data.split(":")[1]  # "video" or "audio"

    # The original URL is in the message we replied to.
    original = callback.message.reply_to_message
    if not original or not original.text:
        await callback.answer("Original link not found. Please send it again.", show_alert=True)
        return

    url = original.text
    await callback.answer()  # stop the button's loading spinner

    status_msg = await callback.message.answer("⌛ ")
    filepath = None
    try:
        filepath = await asyncio.to_thread(download_video, url, media_type)

        media_file = FSInputFile(filepath)
        if media_type == "audio":
            await callback.message.answer_audio(audio=media_file)
        else:
            await callback.message.answer_video(video=media_file)

    except ValueError as e:
        if str(e) == "file_too_large":
            logger.info("File too large for %s", url)
            await callback.message.answer("❌ This is too large (over 50MB). Try a shorter one.")
        else:
            logger.exception("Unexpected value error for %s", url)
            await callback.message.answer("❌ Something went wrong. Please try again later.")
    except yt_dlp.utils.DownloadError as e:
        logger.error("Download failed for %s: %s", url, e)
        await callback.message.answer("❌ Couldn't download this. It may be private, removed, or unavailable.")
    except Exception:
        logger.exception("Unexpected error for %s", url)
        await callback.message.answer("❌ Something went wrong. Please try again later.")
    finally:
        await status_msg.delete()
        cleanup(filepath)


@router.message()
async def handle_links(message: Message):
    url = message.text
    if not url:
        return

    if any(domain in url for domain in SUPPORTED_DOMAINS):
        # Show format choice instead of downloading immediately.
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🎬 Video", callback_data="dl:video"),
            InlineKeyboardButton(text="🎧 Audio", callback_data="dl:audio"),
        ]])
        # Reply to the user's message so the callback can read the URL back.
        await message.reply("Choose a format:", reply_markup=keyboard)
    else:
        await message.answer("Please, send me a correct link of YouTube or Instagram.")

