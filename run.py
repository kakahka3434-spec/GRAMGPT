"""
GRAMGPT — Startup script.
Starts the API server (FastAPI) and optionally the bot (aiogram).
"""

import asyncio
import logging
import os
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("gramgpt")


def check_env():
    """Check .env.local exists and has required fields."""
    from src.config import settings

    missing = []
    if not settings.telegram_api_id:
        missing.append("TELEGRAM_API_ID")
    if not settings.telegram_api_hash:
        missing.append("TELEGRAM_API_HASH")
    if not settings.telegram_phone:
        missing.append("TELEGRAM_PHONE")
    if not any([settings.openai_api_key, settings.openrouter_api_key, settings.groq_api_key]):
        missing.append("OPENAI_API_KEY / OPENROUTER_API_KEY / GROQ_API_KEY")

    if missing:
        logger.warning("Missing credentials (set in .env.local):")
        for m in missing:
            logger.warning(f"  - {m}")
        logger.warning("Some features will be unavailable until these are configured.")
    else:
        logger.info("All credentials configured. ✓")


def main():
    import uvicorn

    check_env()

    logger.info("=" * 50)
    logger.info("GRAMGPT Starting...")
    logger.info("=" * 50)

    # Check Redis
    try:
        import socket
        s = socket.create_connection(("localhost", 6379), timeout=1)
        s.close()
        logger.info("Redis available → distributed task queue")
    except Exception:
        logger.info("Redis not available → inline task execution (no Redis needed)")

    # Start API
    port = int(os.getenv("PORT", "8000"))
    logger.info(f"API server → http://localhost:{port}")
    logger.info(f"Swagger docs → http://localhost:{port}/docs")
    logger.info(f"Mini App → http://localhost:{port}/panel")
    logger.info(f"Landing → http://localhost:{port}/")
    logger.info(f"Health → http://localhost:{port}/api/v1/health")
    logger.info("=" * 50)

    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info",
    )


if __name__ == "__main__":
    main()
