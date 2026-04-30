from aiogram import Router, types
from aiogram.filters import Command
from src.utils.memory import memory

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Hello! I am GRAMGPT, your AI-powered Telegram assistant.\n\n"
        "Send me a message and I will reply using GPT-4! I remember our recent conversation."
    )

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "📜 **Help Menu**\n\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/clear - Clear conversation history\n"
        "Just send any text to chat with the AI!"
    )

@router.message(Command("clear"))
async def cmd_clear(message: types.Message):
    memory.clear_history(message.chat.id)
    await message.answer("🧹 Conversation history has been cleared!")
