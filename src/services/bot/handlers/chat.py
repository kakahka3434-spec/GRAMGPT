import asyncio
import logging
from aiogram import Router, types, F
from src.core.openai_client import openai_client
from src.db.memory import memory
from src.core.human_emulation import human_engine
from src.config import settings
from src.db.database import db

logger = logging.getLogger(__name__)

router = Router()


@router.message(F.text)
async def handle_text_message(message: types.Message):
    try:
        if settings.human_emulation_enabled:
            await human_engine.wait_before_action(0.5, 2.0)

        await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

        memory.add_message(message.chat.id, "user", message.text)
        history = memory.get_history(message.chat.id)

        response = await openai_client.get_chat_response(message.chat.id, history)

        if settings.human_emulation_enabled:
            delay = await human_engine.get_typing_delay(response)
            await asyncio.sleep(min(delay, 5.0))

        memory.add_message(message.chat.id, "assistant", response)
        await message.answer(response)
    except Exception as e:
        logger.error(f"Error handling text message from {message.chat.id}: {e}")
        await message.answer("Произошла ошибка при обработке сообщения. Попробуйте ещё раз.")


@router.message()
async def handle_unsupported_message(message: types.Message):
    await message.answer("Отправьте текст, фото или голосовое сообщение.")
