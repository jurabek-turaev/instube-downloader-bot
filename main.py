import asyncio
import logging
import os

from config import DOWNLOADS_DIR, bot, dp
from handlers import audio, commands, links, video

logger = logging.getLogger(__name__)


async def main():
    os.makedirs(DOWNLOADS_DIR, exist_ok=True)

    # Router order defines handler priority: specific media types must come
    # before links.router, whose catch-all @router.message() would otherwise
    # swallow every message.
    dp.include_router(commands.router)
    dp.include_router(audio.router)
    dp.include_router(video.router)
    dp.include_router(links.router)

    logger.info("Bot started...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())