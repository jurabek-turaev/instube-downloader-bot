import asyncio
import logging

from aiogram import F, Router
from aiogram.types import FSInputFile, Message

from config import DOWNLOADS_DIR, VIDEO_NOTE_MAX_DURATION, bot
from services.converter import convert_to_video_note
from utils.files import cleanup, is_too_large

logger = logging.getLogger(__name__)
router = Router()


@router.message(F.video)
async def video_to_note(message: Message):
    video = message.video

    if is_too_large(video.file_size):
        await message.reply("❌ This file is too large (over 50MB).")
        return

    # Video notes are capped by Telegram; tell the user we'll trim it.
    if video.duration and video.duration > VIDEO_NOTE_MAX_DURATION:
        await message.answer(
            f"ℹ️ Video notes can't be longer than {VIDEO_NOTE_MAX_DURATION} seconds. "
            f"Only the first {VIDEO_NOTE_MAX_DURATION} seconds will be used."
        )

    status_msg = await message.reply("⌛ Converting to video note...")

    src_path = f"{DOWNLOADS_DIR}/{video.file_id}_src.mp4"
    note_path = f"{DOWNLOADS_DIR}/{video.file_id}_note.mp4"
    try:
        await bot.download(video, destination=src_path)
        await asyncio.to_thread(convert_to_video_note, src_path, note_path)
        await message.answer_video_note(video_note=FSInputFile(note_path))
    except Exception:
        logger.exception("Video -> video note conversion failed")
        await message.answer("❌ Couldn't convert this video. Please try again.")
    finally:
        await status_msg.delete()
        cleanup(src_path, note_path)


@router.message(F.video_note)
async def note_to_video(message: Message):
    video_note = message.video_note

    if is_too_large(video_note.file_size):
        await message.reply("❌ This file is too large (over 50MB).")
        return

    status_msg = await message.reply("⌛ Converting to video...")

    mp4_path = f"{DOWNLOADS_DIR}/{video_note.file_id}.mp4"
    try:
        # Video notes are already mp4 — no conversion needed, just resend
        # them as a regular video.
        await bot.download(video_note, destination=mp4_path)
        await message.answer_video(video=FSInputFile(mp4_path, filename="video.mp4"))
    except Exception:
        logger.exception("Video note -> mp4 conversion failed")
        await message.answer("❌ Couldn't convert this video note. Please try again.")
    finally:
        await status_msg.delete()
        cleanup(mp4_path)
