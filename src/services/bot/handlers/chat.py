import asyncio
from aiogram import Router, types, F
from src.core.openai_client import openai_client
from src.db.memory import memory
from src.core.human_emulation import human_engine
from src.config import settings
from src.core.neuro_modules import neuro_chatting
from src.db.database import db
from src.core.crm_sync import crm_sync

router = Router()

@router.message(F.text)
async def handle_text_message(message: types.Message):
    sub = db.get_subscription(message.chat.id)
    is_free = sub.get("plan") == "free"

    if settings.human_emulation_enabled:
        await human_engine.wait_before_action(1.0, 3.0)

    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

    memory.add_message(message.chat.id, "user", message.text)
    history = memory.get_history(message.chat.id)

    response = await openai_client.get_chat_response(message.chat.id, history)

    # CRM Sync Logic
    if "купить" in message.text.lower() or "цена" in message.text.lower():
        lead_data = {"username": message.from_user.username, "chat_id": message.chat.id}
        await crm_sync.sync_lead(lead_data)

    if is_free:
        response += "\n\n---\n⚡ *Отправлено через GPTGRAM Ultimate*"

    if settings.human_emulation_enabled:
        delay = await human_engine.get_typing_delay(response)
        await asyncio.sleep(min(delay, 8.0))

    memory.add_message(message.chat.id, "assistant", response)
    await message.answer(response)

@router.message()
async def handle_unsupported_message(message: types.Message):
    await message.answer("😅 Пока я работаю только с текстом в этом режиме.")
