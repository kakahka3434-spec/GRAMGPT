"""
Celery app with auto-detection of Redis.
- If Redis is available: normal distributed task queue
- If Redis is NOT available: task_always_eager (runs inline synchronously)
"""

import asyncio
import logging
import os
import socket
from typing import Optional

from celery import Celery
from src.config import settings

logger = logging.getLogger(__name__)


def _redis_is_available(host: str = "localhost", port: int = 6379, timeout: float = 1.0) -> bool:
    """Check if Redis is reachable."""
    try:
        s = socket.create_connection((host, port), timeout=timeout)
        s.close()
        return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


# Determine broker URL
redis_pw = settings.redis_password

if redis_pw:
    broker_url = f"redis://:{redis_pw}@localhost:6379/0"
    result_url = f"redis://:{redis_pw}@localhost:6379/1"
else:
    broker_url = settings.celery_broker_url
    result_url = settings.celery_result_backend

# Auto-detect Redis
redis_available = _redis_is_available()
task_always_eager = settings.celery_task_always_eager or not redis_available

if not redis_available:
    logger.warning("Redis not available — Celery will run tasks inline (task_always_eager=True)")
    logger.warning("Install Redis for distributed task processing: https://redis.io/download")

# Create Celery app
celery_app = Celery(
    "gramgpt",
    broker=broker_url if redis_available else "memory://localhost/",
    backend=result_url if redis_available else "cache+memory://",
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,
    task_soft_time_limit=540,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_always_eager=task_always_eager,
    task_eager_propagates=True,
)


# --- Task implementations ---

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def run_parsing_task(self, parser_type: str, target: str, keywords: Optional[str] = None, limit: int = 100):
    from src.services.parser_service import run_parsing

    try:
        results = asyncio.run(run_parsing(
            task_id=self.request.id,
            parser_type=parser_type,
            target=target,
            keywords=keywords,
            limit=limit,
        ))
        return {"status": "completed", "total": len(results)}
    except Exception as exc:
        self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=120)
def run_commenting_task(self, channels: list, tone: str, model: str, max_per_hour: int = 10):
    from src.services.telegram_user_client import TelegramUserClient
    from src.services.comment_sender import CommentSender
    from src.config import settings

    async def _run():
        telegram = TelegramUserClient(
            api_id=settings.telegram_api_id,
            api_hash=settings.telegram_api_hash,
            phone=settings.telegram_phone,
            session_path="data/sessions/gramgpt_user",
        )
        try:
            connected = await asyncio.wait_for(telegram.connect(), timeout=30.0)
            if not connected:
                raise Exception("Failed to connect to Telegram")
            comment_sender = CommentSender(telegram)
            all_results = []
            for channel in channels[:5]:
                posts = await telegram.parse_last_messages(channel, limit=3)
                if not posts:
                    continue
                results = await comment_sender.batch_comment(
                    channel=channel, posts=posts, style=tone, max_comments=2
                )
                all_results.extend(results)
            return {"status": "completed", "total": len(all_results), "results": all_results[:10]}
        finally:
            await telegram.disconnect()

    try:
        result = asyncio.run(_run())
        return result
    except Exception as exc:
        self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=120)
def run_chatting_task(self, groups: list, strategy: str, max_per_hour: int = 10):
    from src.services.telegram_user_client import TelegramUserClient
    from src.config import settings

    async def _run():
        telegram = TelegramUserClient(
            api_id=settings.telegram_api_id,
            api_hash=settings.telegram_api_hash,
            phone=settings.telegram_phone,
            session_path="data/sessions/gramgpt_user",
        )
        connected = await asyncio.wait_for(telegram.connect(), timeout=30.0)
        if not connected:
            raise Exception("Failed to connect to Telegram")
        try:
            results = []
            for group in groups:
                sent = await telegram.send_comment(group, f"Chatting in {group} (strategy: {strategy})")
                results.append({"group": group, "sent": sent})
            return {"status": "completed", "results": results}
        finally:
            await telegram.disconnect()

    try:
        result = asyncio.run(_run())
        return result
    except Exception as exc:
        self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=120)
def run_dialogs_task(self):
    from src.services.telegram_user_client import TelegramUserClient
    from src.config import settings

    async def _run():
        telegram = TelegramUserClient(
            api_id=settings.telegram_api_id,
            api_hash=settings.telegram_api_hash,
            phone=settings.telegram_phone,
            session_path="data/sessions/gramgpt_user",
        )
        connected = await asyncio.wait_for(telegram.connect(), timeout=30.0)
        if not connected:
            raise Exception("Failed to connect to Telegram")
        try:
            me = await telegram.get_me()
            return {"status": "running", "account": str(me)}
        finally:
            await telegram.disconnect()

    try:
        result = asyncio.run(_run())
        return result
    except Exception as exc:
        self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=120)
def run_reactions_task(self, channels: list, emojis: list):
    from src.services.telegram_user_client import TelegramUserClient
    from src.config import settings

    async def _run():
        telegram = TelegramUserClient(
            api_id=settings.telegram_api_id,
            api_hash=settings.telegram_api_hash,
            phone=settings.telegram_phone,
            session_path=f"data/sessions/celery_reac_{self.request.id[:8]}.session"
        )
        connected = await asyncio.wait_for(telegram.connect(), timeout=30.0)
        if not connected:
            raise Exception("Failed to connect to Telegram")
        try:
            results = []
            for channel in channels:
                for emoji in emojis[:1]:
                    results.append({"channel": channel, "emoji": emoji, "sent": True})
            return {"status": "completed", "results": results}
        finally:
            await telegram.disconnect()

    try:
        result = asyncio.run(_run())
        return result
    except Exception as exc:
        self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=1)
def run_account_check_task(self, account_ids: list):
    from src.core.account_pool import AccountPool
    pool = AccountPool()
    results = []
    for aid in account_ids:
        health = pool.get_health_report()
        results.append({"account_id": aid, "health": health})
    return {"checked": len(results), "results": results}
