from aiogram import Router, types, F
from src.utils.openai_client import openai_client
from src.utils.memory import memory

router = Router()

@router.message(F.text)
async def handle_text_message(message: types.Message):
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    memory.add_message(message.chat.id, "user", message.text)
    history = memory.get_history(message.chat.id)
    response = await openai_client.get_chat_response(message.chat.id, history)
    memory.add_message(message.chat.id, "assistant", response)
    await message.answer(response)

@router.message()
async def handle_unsupported_message(message: types.Message):
    await message.answer("😅 На данный момент я поддерживаю только текстовые сообщения. Пожалуйста, напишите мне что-нибудь!")
