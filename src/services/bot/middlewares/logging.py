import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        if isinstance(event, Message):
            user = event.from_user
            logger.info(f"Received message from {user.full_name} ({user.id}): {event.text[:50]}...")

        result = await handler(event, data)

        if isinstance(event, Message):
            logger.info(f"Handled message from {user.id}")

        return result
