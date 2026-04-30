import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand

from src.config import settings
from src.handlers import commands, chat, media
from src.middlewares.logging import LoggingMiddleware

async def set_commands(bot: Bot):
    commands_list = [
        BotCommand(command="start", description="🚀 Get started"),
        BotCommand(command="image", description="🎨 Generate AI image"),
        BotCommand(command="clear", description="🧹 Clear history"),
        BotCommand(command="help", description="📜 Help info"),
    ]
    await bot.set_my_commands(commands_list)

async def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout
    )

    # Initialize bot and dispatcher
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )
    dp = Dispatcher()

    # Register middlewares
    dp.message.middleware(LoggingMiddleware())

    # Register routers
    dp.include_router(commands.router)
    dp.include_router(media.router)
    dp.include_router(chat.router)

    # Set bot commands menu
    await set_commands(bot)

    # Start polling
    logging.info("Starting GRAMGPT Ultimate...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot stopped")
