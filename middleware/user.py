import asyncio
import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from services.database import upsert_user

logger = logging.getLogger(__name__)


class UserMiddleware(BaseMiddleware):
    """Save/update the user in the DB on every incoming message."""

    async def __call__(
            self,
            handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: dict[str, Any],
    ) -> Any:
        user = event.from_user
        if user and not user.is_bot:
            try:
                await asyncio.to_thread(
                    upsert_user,
                    user.id, user.username, user.full_name, user.language_code,
                )
            except Exception:
                logger.exception("Failed to save user %s", user.id)

        return await handler(event, data)