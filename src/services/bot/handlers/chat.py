import asyncio
from aiogram import Router, types, F
from src.core.openai_client import openai_client
from src.db.memory import memory
from src.core.human_emulation import human_engine
from src.config import settings
from src.core.neuro_modules import neuro_chatting

router = Router()

@router.message(F.text)
async def handle_text_message(message: types.Message):
    # GPTGRAM Ultimate: Human Emulation Pre-delay
    if settings.human_emulation_enabled:
        await human_engine.wait_before_action(1.0, 3.0)

    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

    memory.add_message(message.chat.id, "user", message.text)
    history = memory.get_history(message.chat.id)

    # NeuroChatting: Handle objections or general chat
    if any(word in message.text.lower() for word in ["дорого", "нет времени", "сомневаюсь"]):
        response = await neuro_chatting.handle_objection(message.text, history)
    else:
        response = await openai_client.get_chat_response(message.chat.id, history)

    # GPTGRAM Ultimate: Realistic Typing Delay
    if settings.human_emulation_enabled:
        delay = await human_engine.get_typing_delay(response)
        await asyncio.sleep(min(delay, 8.0)) # Capped at 8s

    memory.add_message(message.chat.id, "assistant", response)
    await message.answer(response)

@router.message()
async def handle_unsupported_message(message: types.Message):
    await message.answer("😅 Пока я работаю только с текстом в этом режиме.")
