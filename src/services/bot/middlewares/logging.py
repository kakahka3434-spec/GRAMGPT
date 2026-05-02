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
        user_id = None
        if isinstance(event, Message) and event.from_user:
            user_id = event.from_user.id
            text_preview = (event.text or "")[:50]
            logger.info(f"Received message from {event.from_user.full_name} ({user_id}): {text_preview}")

        result = await handler(event, data)

        if isinstance(event, Message) and user_id:
            logger.info(f"Handled message from {user_id}")

        return result
