from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile, Message
from dotenv import load_dotenv
import asyncio
import os 
import yt_dlp

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

def download_video(url: str) -> str:
    ydl_opts = {
        'format': 'b[ext=mp4]/b', 
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'max_filesize': 52428800,
        'quiet': True,
        'no_warnings': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        return filename

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Hi there! Send me any YouTube or Instagram link, and I will download for you.")

@dp.message()
async def handle_links(message: Message):
    url = message.text

    if "youtube.com" in url or "youtu.be" in url or "instagram.com" in url:
        status_msg = await message.answer("⌛")

        try:
            filepath = await asyncio.to_thread(download_video, url)

            video_file = FSInputFile(filepath)
            await message.answer_video(video=video_file)

            os.remove(filepath)
        
        except Exception as e:
            await message.answer("❌ There's an error occured. Maybe video size more than 50MB or link is relevant to private profile.")
        finally:
            await status_msg.delete()
    
    else:
        await message.answer("Please, send me a correct link of YouTube or Instagram.")

async def main():
    os.makedirs("downloads", exist_ok=True)
    print("Bot started...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())