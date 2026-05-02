import os
import asyncio
import uvicorn
import logging
import sys
from multiprocessing import Process
from src.api.main import app
from src.services.bot.main import main as start_bot

def run_api():
    uvicorn.run(app, host="0.0.0.0", port=8000)

async def run_combined():
    # Run API and Bot concurrently in the same event loop if possible,
    # or use Process for isolation.
    # Since both use asyncio, let's try starting bot as a task.

    # We need to import the bot initialization logic
    from aiogram import Bot, Dispatcher
    from aiogram.enums import ParseMode
    from aiogram.client.default import DefaultBotProperties
    from src.config import settings
    from src.services.bot.handlers import commands, chat, media
    from src.services.bot.middlewares.logging import LoggingMiddleware
    from src.services.bot.main import set_commands

    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    # Bot Setup
    bot = Bot(token=settings.bot_token or "dummy_token",
              default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
    dp = Dispatcher()
    dp.message.middleware(LoggingMiddleware())
    dp.include_router(commands.router)
    dp.include_router(media.router)
    dp.include_router(chat.router)

    # API Server Config
    config = uvicorn.Config(app, host="0.0.0.0", port=int(os.getenv("PORT", 10000)), log_level="info")
    server = uvicorn.Server(config)

    logging.info("Starting GRAMGPT (API + Bot)...")

    if settings.bot_token and settings.bot_token != "dummy_token":
        await set_commands(bot)
        # Start both tasks
        await asyncio.gather(
            server.serve(),
            dp.start_polling(bot)
        )
    else:
        logging.warning("BOT_TOKEN missing, running API only.")
        await server.serve()

if __name__ == "__main__":
    asyncio.run(run_combined())
