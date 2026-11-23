import asyncio
import logging
import os
from aiogram.types import BotCommand
from config import DOWNLOADS_DIR, bot, dp
from handlers import audio, commands, links, video
from services.database import init_db
from middleware.user import UserMiddleware

logger = logging.getLogger(__name__)
dp.message.middleware(UserMiddleware())

async def main():
    os.makedirs(DOWNLOADS_DIR, exist_ok=True)
    init_db()

    # Router order defines handler priority: specific media types must come
    # before links.router, whose catch-all @router.message() would otherwise
    # swallow every message.
    dp.include_router(commands.router)
    dp.include_router(audio.router)
    dp.include_router(video.router)
    dp.include_router(links.router)

    await bot.set_my_commands([
        BotCommand(command="start", description="Start the bot"),
        BotCommand(command="help", description="How to use the bot"),
    ])
    
    logger.info("Bot started...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())