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

from config import MAX_FILESIZE
from services.downloader import MultipleMediaError, download_images, download_video
from utils.files import cleanup, cleanup_dir
from services.database import increment_downloads

logger = logging.getLogger(__name__)
router = Router()

YOUTUBE_DOMAINS = ("youtube.com", "youtu.be")
INSTAGRAM_DOMAINS = ("instagram.com",)
IMAGE_EXTS = (".jpeg", ".jpg", ".png", ".webp", ".heic")

CAPTION = "📥 Downloaded via @instubedownloaderbot"
ALBUM_LIMIT = 10  # Telegram allows at most 10 items per media group


def _is_image(path: str) -> bool:
    return path.lower().endswith(IMAGE_EXTS)


async def send_media_files(message: Message, files: list[str]) -> int:
    """Send photos/videos (one by one or as albums). Returns how many were sent."""
    sendable = [f for f in files if os.path.getsize(f) <= MAX_FILESIZE]
    skipped = len(files) - len(sendable)

    if len(sendable) == 1:
        path = sendable[0]
        if _is_image(path):
            await message.answer_photo(photo=FSInputFile(path), caption=CAPTION)
        else:
            await message.answer_video(video=FSInputFile(path), caption=CAPTION)
    else:
        for i in range(0, len(sendable), ALBUM_LIMIT):
            album = MediaGroupBuilder(caption=CAPTION)
            for path in sendable[i:i + ALBUM_LIMIT]:
                if _is_image(path):
                    album.add_photo(media=FSInputFile(path))
                else:
                    album.add_video(media=FSInputFile(path))
            await message.answer_media_group(media=album.build())

    if skipped:
        await message.answer(f"⚠️ {skipped} item(s) were skipped: larger than 50MB.")

    return len(sendable)


async def handle_story(message: Message, url: str):
    """Instagram story: download the single item and send it as video or photo."""
    status_msg = await message.answer("⌛")
    image_dir = None
    try:
        files = await asyncio.to_thread(download_images, url)
        if not files:
            await message.answer("❌ Couldn't find this story. It may have expired.")
            return
        image_dir = os.path.dirname(files[0])

        if await send_media_files(message, files[:1]):
            await asyncio.to_thread(increment_downloads, message.from_user.id)

    except Exception:
        logger.exception("Story download failed for %s", url)
        await message.answer("❌ Couldn't download this story. It may be private or expired.")
    finally:
        await status_msg.delete()
        if image_dir:
            cleanup_dir(image_dir)


async def download_and_send(message: Message, user_id: int, url: str, media_type: str):
    """Download a link and send it, with a status message and cleanup.

    `user_id` is passed explicitly: when called from a button, `message` is
    the bot's own message, so `message.from_user` would be the bot.
    """
    status_msg = await message.answer("⌛")
    filepath = None

    try:
        filepath = await asyncio.to_thread(download_video, url, media_type)

        media_file = FSInputFile(filepath)
        if media_type == "audio":
            await message.answer_audio(audio=media_file, caption=CAPTION)
        else:
            await message.answer_video(video=media_file, caption=CAPTION)

        await asyncio.to_thread(increment_downloads, user_id)

    except ValueError as e:
        if str(e) == "file_too_large":
            logger.info("File too large for %s", url)
            await message.answer("❌ This is too large (over 50MB). Try a shorter one.")
        else:
            logger.exception("Unexpected value error for %s", url)
            await message.answer("❌ Something went wrong. Please try again later.")

    except MultipleMediaError:
        await message.answer("❌ Playlists aren't supported. Please send a link to a single video.")
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
    """Instagram: try a single video first; photo posts and carousels go to gallery-dl."""
    status_msg = await message.answer("⌛")
    image_dir = None
    filepath = None
    try:
        try:
            filepath = await asyncio.to_thread(download_video, url, "video")
            await message.answer_video(video=FSInputFile(filepath), caption=CAPTION)
            await asyncio.to_thread(increment_downloads, message.from_user.id)
            return
        except MultipleMediaError:
            pass  # carousel: gallery-dl returns every photo and video in it
        except yt_dlp.utils.DownloadError as e:
            if "No video formats" not in str(e):
                raise

        files = await asyncio.to_thread(download_images, url)
        if not files:
            await message.answer("❌ Couldn't find anything to download in this post.")
            return
        image_dir = os.path.dirname(files[0])

        if await send_media_files(message, files):
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

    await download_and_send(callback.message, callback.from_user.id, url, media_type)


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
        if "/stories/" in url:
            await handle_story(message, url)
        else:
            await handle_instagram(message, url)

    else:
        await message.answer("Please, send me a correct link of YouTube or Instagram.")

