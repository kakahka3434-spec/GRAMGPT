from aiogram import Router, types
from src.utils.openai_client import openai_client

router = Router()

@router.message()
async def handle_message(message: types.Message):
    if not message.text:
        return

    # Show "typing" status while waiting for OpenAI
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

    response = await openai_client.get_chat_response(message.text)
    await message.answer(response)
