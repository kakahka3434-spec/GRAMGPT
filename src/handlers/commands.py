from aiogram import Router, types
from aiogram.filters import Command, CommandObject
from src.utils.memory import memory
from src.utils.openai_client import openai_client

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🚀 **Welcome to GRAMGPT Ultimate!**\n\n"
        "I am much more powerful than any other bot. I can:\n"
        "💬 **Chat** with context\n"
        "🎨 **Generate Images** with /image\n"
        "👁️ **See** photos you send me\n"
        "🎤 **Hear** your voice messages\n"
        "🧹 **Clear** history with /clear"
    )

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "📜 **Ultimate Command List**\n\n"
        "/start - Welcome message\n"
        "/image <prompt> - Generate an AI image\n"
        "/clear - Reset conversation history\n"
        "/help - Show this list"
    )

@router.message(Command("clear"))
async def cmd_clear(message: types.Message):
    memory.clear_history(message.chat.id)
    await message.answer("🧹 History cleared. I am ready for a fresh start!")

@router.message(Command("image"))
async def cmd_image(message: types.Message, command: CommandObject):
    if not command.args:
        await message.answer("Please provide a prompt for the image, e.g., `/image a futuristic city`")
        return

    await message.bot.send_chat_action(chat_id=message.chat.id, action="upload_photo")
    image_url = await openai_client.generate_image(command.args)

    if image_url.startswith("❌"):
        await message.answer(image_url)
    else:
        await message.answer_photo(photo=image_url, caption=f"🎨 Generated: {command.args}")
