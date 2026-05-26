"""
GRAMGPT entry point — runs API server (FastAPI) and optionally the bot (aiogram).
Used by Render.com (start command: python src/app.py) and local development.
"""

import os
import asyncio
import uvicorn
import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

logger = logging.getLogger("gramgpt")

async def run_combined():
    from src.api.main import app
    from src.config import settings

    port = int(os.getenv("PORT", 10000))

    logger.info("=" * 50)
    logger.info("GRAMGPT starting...")
    logger.info(f"API → http://0.0.0.0:{port}")
    logger.info(f"Docs → http://0.0.0.0:{port}/docs")
    logger.info(f"Health → http://0.0.0.0:{port}/api/v1/health")
    logger.info("=" * 50)

    # Start API
    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)

    # Optionally start bot
    if settings.bot_token and settings.bot_token != "dummy_token":
        from aiogram import Bot, Dispatcher
        from aiogram.enums import ParseMode
        from aiogram.client.default import DefaultBotProperties
        from src.services.bot.handlers import commands, chat, media
        from src.services.bot.middlewares.logging import LoggingMiddleware
        from src.services.bot.main import set_commands

        bot = Bot(token=settings.bot_token,
                  default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
        dp = Dispatcher()
        dp.message.middleware(LoggingMiddleware())
        dp.include_router(commands.router)
        dp.include_router(media.router)
        dp.include_router(chat.router)

        await set_commands(bot)
        logger.info("Bot handlers registered, starting polling...")
        await asyncio.gather(server.serve(), dp.start_polling(bot))
    else:
        logger.info("BOT_TOKEN not set — running API only")
        await server.serve()

if __name__ == "__main__":
    asyncio.run(run_combined())
