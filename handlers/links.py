import os
import asyncio
import logging

import yt_dlp
from aiogram import F, Router
from aiogram.utils.media_group import MediaGroupBuilder
from aiogram.types import (
    CallbackQuery, FSInputFile, InlineKeyboardButton,
    InlineKeyboardMarkup, Message,
)

from services.downloader import download_video, download_images
from utils.files import cleanup, cleanup_dir
from services.database import increment_downloads

logger = logging.getLogger(__name__)
router = Router()

YOUTUBE_DOMAINS = ("youtube.com", "youtu.be")
INSTAGRAM_DOMAINS = ("instagram.com",)


async def download_and_send(message: Message, url: str, media_type: str):
    """Download a link and send it, with a status message and cleanup."""
    status_msg = await message.answer("⌛")
    filepath = None

    try:
        filepath = await asyncio.to_thread(download_video, url, media_type)

        media_file = FSInputFile(filepath)
        if media_type == "audio":
            await message.answer_audio(audio=media_file)
        else:
            await message.answer_video(video=media_file)

        await asyncio.to_thread(increment_downloads, message.from_user.id)

    except ValueError as e:
        if str(e) == "file_too_large":
            logger.info("File too large for %s", url)
            await message.answer("❌ This is too large (over 50MB). Try a shorter one.")
        else:
            logger.exception("Unexpected value error for %s", url)
            await message.answer("❌ Something went wrong. Please try again later.")

    except yt_dlp.utils.DownloadError as e:
        logger.error("Download failed for %s: %s", url, e)
        await message.answer("❌ Couldn't download this. It may be private, removed, or unavailable.")
    except Exception:
        logger.exception("Unexpected error for %s", url)
        await message.answer("❌ Something went wrong. Please try again later.")
    finally:
        await status_msg.delete()
        cleanup(filepath)


async def handle_instagram(message: Message, url: str):
    """Instagram: try video first, fall back to images for photo posts."""
    status_msg = await message.answer("⌛")
    image_dir = None
    filepath = None
    try:
        try:
            filepath = await asyncio.to_thread(download_video, url, "video")
            await message.answer_video(video=FSInputFile(filepath))
            await asyncio.to_thread(increment_downloads, message.from_user.id)
            return
        except yt_dlp.utils.DownloadError as e:
            if "No video formats" not in str(e):
                raise

        files = await asyncio.to_thread(download_images, url)
        if not files:
            await message.answer("❌ Couldn't find anything to download in this post.")
            return
        image_dir = os.path.dirname(files[0])

        album = MediaGroupBuilder()
        for path in files:
            album.add_photo(media=FSInputFile(path))
        await message.answer_media_group(media=album.build())
        await asyncio.to_thread(increment_downloads, message.from_user.id)

    except ValueError as e:
        if str(e) == "file_too_large":
            await message.answer("❌ This is too large (over 50MB). Try a shorter one.")
        else:
            logger.exception("Unexpected value error for %s", url)
            await message.answer("❌ Something went wrong. Please try again later.")
    except Exception:
        logger.exception("Instagram download failed for %s", url)
        await message.answer("❌ Couldn't download this. It may be private, removed, or unavailable.")
    finally:
        await status_msg.delete()
        cleanup(filepath)
        if image_dir:
            cleanup_dir(image_dir)


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

    await callback.message.delete()

    await download_and_send(callback.message, url, media_type)


@router.message()
async def handle_links(message: Message):
    url = message.text
    if not url:
        return

    if any(domain in url for domain in YOUTUBE_DOMAINS):
        # Show format choice instead of downloading immediately.
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🎬 Video", callback_data="dl:video", style="success"),
            InlineKeyboardButton(text="🎧 Audio", callback_data="dl:audio", style="primary"),
        ]])
        # Reply to the user's message so the callback can read the URL back.
        await message.reply("Choose a format:", reply_markup=keyboard)

    elif any(domain in url for domain in INSTAGRAM_DOMAINS):
        await handle_instagram(message, url)

    else:
        await message.answer("Please, send me a correct link of YouTube or Instagram.")

