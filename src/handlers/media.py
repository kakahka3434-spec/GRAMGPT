import os
from aiogram import Router, types, F
from src.utils.openai_client import openai_client
from src.utils.memory import memory
import base64

router = Router()

@router.message(F.voice)
async def handle_voice(message: types.Message):
    await message.bot.send_chat_action(chat_id=message.chat.id, action="record_voice")
    file_id = message.voice.file_id
    file = await message.bot.get_file(file_id)
    temp_voice_path = f"temp_{file_id}.ogg"
    await message.bot.download_file(file.file_path, destination=temp_voice_path)
    transcription = await openai_client.transcribe_voice(temp_voice_path)
    os.remove(temp_voice_path)

    if transcription.startswith("❌"):
        await message.answer(transcription)
        return

    await message.reply(f"🎤 **Транскрипция:**\n_{transcription}_")
    memory.add_message(message.chat.id, "user", transcription)
    response = await openai_client.get_chat_response(memory.get_history(message.chat.id))
    memory.add_message(message.chat.id, "assistant", response)
    await message.answer(response)

@router.message(F.photo)
async def handle_photo(message: types.Message):
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    temp_photo_path = f"temp_{photo.file_id}.jpg"
    await message.bot.download_file(file.file_path, destination=temp_photo_path)

    with open(temp_photo_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')
    os.remove(temp_photo_path)

    user_prompt = message.caption or "Что на этом изображении?"
    messages = [{"role": "user", "content": [
        {"type": "text", "text": user_prompt},
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
    ]}]
    response = await openai_client.get_chat_response(messages)
    await message.reply(response)
