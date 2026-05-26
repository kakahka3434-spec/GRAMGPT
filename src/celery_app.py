import os
from celery import Celery
from src.config import settings

redis_pw = settings.redis_password
if redis_pw:
    broker_url = f"redis://:{redis_pw}@localhost:6379/0"
    result_url = f"redis://:{redis_pw}@localhost:6379/1"
else:
    broker_url = settings.celery_broker_url
    result_url = settings.celery_result_backend

celery_app = Celery(
    "gramgpt",
    broker=broker_url,
    backend=result_url,
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
)

import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def run_parsing_task(self, parser_type: str, target: str, keywords: Optional[str] = None, limit: int = 100):
    """Run parsing in background Celery task."""
    import json
    import sqlite3
    from datetime import datetime
    from src.services.telegram_user_client import TelegramUserClient
    from src.services.channel_discovery import ChannelDiscovery
    from src.config import settings

    async def _run():
        telegram = TelegramUserClient(
            api_id=settings.telegram_api_id,
            api_hash=settings.telegram_api_hash,
            phone=settings.telegram_phone,
            session_path=f"data/sessions/celery_parse_{self.request.id[:8]}.session"
        )
        try:
            connected = await asyncio.wait_for(telegram.connect(), timeout=30.0)
            if not connected:
                raise Exception("Failed to connect to Telegram")
            discovery = ChannelDiscovery(telegram)
            kw = keywords.split(",") if keywords else [target]
            results = await discovery.search_by_keywords(kw, limit=min(limit, 50))
            results = await discovery.filter_open_comments(results)
            return results
        finally:
            await telegram.disconnect()

    try:
        results = asyncio.run(_run())
        tasks_db = "data/tasks.db"
        os.makedirs("data", exist_ok=True)
        with sqlite3.connect(tasks_db) as conn:
            conn.execute(
                "UPDATE tasks SET status = ?, completed_at = ?, results = ? WHERE task_id = ?",
                ("completed", datetime.now().isoformat(), json.dumps(results), self.request.id)
            )
            conn.commit()
        return {"status": "completed", "total": len(results)}
    except Exception as exc:
        self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=120)
def run_commenting_task(self, channels: list, tone: str, model: str, max_per_hour: int = 10):
    """Run commenting campaign in background Celery task."""
    from src.services.telegram_user_client import TelegramUserClient
    from src.services.comment_sender import CommentSender
    from src.core.pipeline_orchestrator import PipelineOrchestrator
    from src.config import settings

    async def _run():
        telegram = TelegramUserClient(
            api_id=settings.telegram_api_id,
            api_hash=settings.telegram_api_hash,
            phone=settings.telegram_phone,
            session_path=f"data/sessions/celery_comment_{self.request.id[:8]}.session"
        )
        try:
            connected = await asyncio.wait_for(telegram.connect(), timeout=30.0)
            if not connected:
                raise Exception("Failed to connect to Telegram")
            comment_sender = CommentSender(telegram)
            orchestrator = PipelineOrchestrator(
                telegram_client=telegram,
                comment_sender=comment_sender,
                settings={"work_mode": tone}
            )
            await orchestrator.start(
                target_channels=channels,
                style=tone,
                max_comments_per_hour=max_per_hour
            )
            while orchestrator.is_running:
                await asyncio.sleep(5)
            return {"status": "completed", "channels": channels}
        finally:
            await telegram.disconnect()

    try:
        result = asyncio.run(_run())
        return result
    except Exception as exc:
        self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=1)
def run_account_check_task(self, account_ids: list):
    """Check health/GGR for accounts in background."""
    from src.core.account_pool import AccountPool
    pool = AccountPool()
    results = []
    for aid in account_ids:
        health = pool.get_health_report()
        results.append({"account_id": aid, "health": health})
    return {"checked": len(results), "results": results}
