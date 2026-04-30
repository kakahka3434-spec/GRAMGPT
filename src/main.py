import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand

from src.config import settings
from src.handlers import commands, chat, media, education
from src.middlewares.logging import LoggingMiddleware

async def set_commands(bot: Bot):
    commands_list = [
        BotCommand(command="start", description="🌲 Старт и приветствие"),
        BotCommand(command="strategy", description="🔍 Глубокая бизнес-стратегия"),
        BotCommand(command="learn", description="🎓 Мои навыки"),
        BotCommand(command="image", description="🎨 Создать бренд-ассет"),
        BotCommand(command="clear", description="🧹 Очистить историю"),
        BotCommand(command="help", description="📜 Помощь"),
    ]
    await bot.set_my_commands(commands_list)

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout
    )

    bot = Bot(
        token=settings.bot_token or "dummy_token",
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )
    dp = Dispatcher()

    dp.message.middleware(LoggingMiddleware())

    dp.include_router(commands.router)
    dp.include_router(education.router)
    dp.include_router(media.router)
    dp.include_router(chat.router)

    if settings.bot_token:
        await set_commands(bot)
        logging.info("Запуск бота EL Solopreneur Strategist...")
        await dp.start_polling(bot)
    else:
        logging.warning("BOT_TOKEN не найден. Бот не запущен.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Бот остановлен")
