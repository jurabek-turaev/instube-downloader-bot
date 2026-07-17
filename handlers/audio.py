import asyncio
import logging
import os
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery, FSInputFile, InlineKeyboardButton,
    InlineKeyboardMarkup, Message,
)

from config import DOWNLOADS_DIR, bot
from services.converter import convert_audio
from utils.files import cleanup, is_too_large

logger = logging.getLogger(__name__)
router = Router()


class VoiceToMp3(StatesGroup):
    waiting_for_filename = State()


@router.message(F.audio)
async def audio_to_voice(message: Message):
    audio = message.audio

    if is_too_large(audio.file_size):
        await message.reply("❌ This file is too large (over 50MB).")
        return

    status_msg = await message.reply("⌛ Converting to voice...")

    mp3_path = f"{DOWNLOADS_DIR}/{audio.file_id}.mp3"
    ogg_path = f"{DOWNLOADS_DIR}/{audio.file_id}.ogg"
    try:
        await bot.download(audio, destination=mp3_path)
        await asyncio.to_thread(convert_audio, mp3_path, ogg_path, "libopus")
        await message.answer_voice(voice=FSInputFile(ogg_path))
    except Exception:
        logger.exception("Audio -> voice conversion failed")
        await message.answer("❌ Couldn't convert this audio. Please try again.")
    finally:
        await status_msg.delete()
        cleanup(mp3_path, ogg_path)


@router.message(F.voice)
async def voice_to_audio(message: Message, state: FSMContext):
    voice = message.voice

    if is_too_large(voice.file_size):
        await message.reply("❌ This file is too large (over 50MB).")
        return

    status_msg = await message.reply("⌛ Converting to mp3...")

    ogg_path = f"{DOWNLOADS_DIR}/{voice.file_id}.ogg"
    mp3_path = f"{DOWNLOADS_DIR}/{voice.file_id}.mp3"
    try:
        await bot.download(voice, destination=ogg_path)
        await asyncio.to_thread(convert_audio, ogg_path, mp3_path, "libmp3lame")

        prompt = await message.answer(
            "📝 Send a name for the mp3 file:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="⏭ Skip", callback_data="name:skip"),
            ]]),
        )
        # Remember the file and the prompt so the next step can use them.
        await state.update_data(mp3_path=mp3_path, prompt_id=prompt.message_id)
        await state.set_state(VoiceToMp3.waiting_for_filename)

    except Exception:
        logger.exception("Voice -> mp3 conversion failed")
        await message.answer("❌ Couldn't convert this voice message. Please try again.")
        await state.clear()
        cleanup(mp3_path)
    finally:
        await status_msg.delete()
        # Only the source ogg goes here; the mp3 is sent after the name step.
        cleanup(ogg_path)


@router.message(VoiceToMp3.waiting_for_filename, F.text)
async def receive_filename(message: Message, state: FSMContext):
    data = await state.get_data()
    mp3_path = data.get("mp3_path")
    prompt_id = data.get("prompt_id")
    await state.clear()

    if prompt_id:
        await bot.delete_message(message.chat.id, prompt_id)

    if not mp3_path or not os.path.exists(mp3_path):
        await message.answer("❌ The file expired. Please send the voice again.")
        return

    # Strip characters that are unsafe in filenames.
    filename = "".join(c for c in message.text if c not in r'\/:*?"<>|').strip()
    filename = filename[:64] or "audio"

    try:
        await message.answer_audio(audio=FSInputFile(mp3_path, filename=f"{filename}.mp3"))
    finally:
        cleanup(mp3_path)


@router.callback_query(VoiceToMp3.waiting_for_filename, F.data == "name:skip")
async def skip_filename(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    mp3_path = data.get("mp3_path")
    await state.clear()
    await callback.answer()
    await callback.message.delete()

    if not mp3_path or not os.path.exists(mp3_path):
        await callback.message.answer("❌ The file expired. Please send the voice again.")
        return

    try:
        await callback.message.answer_audio(audio=FSInputFile(mp3_path, filename="voice.mp3"))
    finally:
        cleanup(mp3_path)
