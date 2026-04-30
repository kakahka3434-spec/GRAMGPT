import asyncio
from aiogram import Router, types, F
from src.core.openai_client import openai_client
from src.db.memory import memory
from src.core.human_emulation import human_engine
from src.config import settings

router = Router()

@router.message(F.text)
async def handle_text_message(message: types.Message):
    # GPTGRAM Ultimate: Human Emulation
    if settings.human_emulation_enabled:
        # 1. Random pause before starting to "type"
        await human_engine.wait_before_action(1.0, 3.0)

    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

    memory.add_message(message.chat.id, "user", message.text)
    history = memory.get_history(message.chat.id)

    response = await openai_client.get_chat_response(message.chat.id, history)

    # 2. Simulate typing delay based on response length
    if settings.human_emulation_enabled:
        delay = await human_engine.get_typing_delay(response)
        await asyncio.sleep(min(delay, 10.0)) # Max 10s delay for UX

    memory.add_message(message.chat.id, "assistant", response)
    await message.answer(response)

@router.message()
async def handle_unsupported_message(message: types.Message):
    await message.answer("😅 На данный момент я поддерживаю только текстовые сообщения.")
