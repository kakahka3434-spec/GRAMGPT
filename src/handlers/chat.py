from aiogram import Router, types, F
from src.utils.openai_client import openai_client
from src.utils.memory import memory

router = Router()

@router.message(F.text)
async def handle_text_message(message: types.Message):
    # Show "typing" status while waiting for OpenAI
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

    # Add user message to memory
    memory.add_message(message.chat.id, "user", message.text)

    # Get response from OpenAI using full history
    history = memory.get_history(message.chat.id)
    response = await openai_client.get_chat_response(history)

    # Add assistant response to memory
    memory.add_message(message.chat.id, "assistant", response)

    await message.answer(response)

@router.message()
async def handle_unsupported_message(message: types.Message):
    await message.answer("😅 I currently only support text messages. Please send me some text!")
