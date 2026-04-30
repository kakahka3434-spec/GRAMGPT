from aiogram import Router, types
from aiogram.filters import Command

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Hello! I am GRAMGPT, your AI-powered Telegram assistant.\n\n"
        "Send me a message and I will reply using GPT-4!"
    )

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "📜 **Help Menu**\n\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "Just send any text to chat with the AI!"
    )
