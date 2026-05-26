"""
Parser Service — runs parsing logic both from Celery and inline.
"""

import asyncio
import json
import logging
import os
import sqlite3
from datetime import datetime
from typing import Optional

from src.config import settings
from src.services.telegram_user_client import TelegramUserClient

logger = logging.getLogger(__name__)


async def run_parsing(
    task_id: str,
    parser_type: str,
    target: str,
    keywords: Optional[str] = None,
    limit: int = 100,
) -> list:
    results = []
    telegram = TelegramUserClient(
        api_id=settings.telegram_api_id,
        api_hash=settings.telegram_api_hash,
        phone=settings.telegram_phone or "",
        session_path=f"data/sessions/parse_{task_id[:8]}.session",
    )
    try:
        connected = await asyncio.wait_for(telegram.connect(), timeout=30.0)
        if not connected:
            logger.error(f"[{task_id}] Failed to connect to Telegram")
            _update_task(task_id, "failed", [], "Connection failed")
            return results

        if parser_type in ("keywords", "channels"):
            from src.services.channel_discovery import ChannelDiscovery

            discovery = ChannelDiscovery(telegram)
            kw = [k.strip() for k in (keywords or target).split(",") if k.strip()]
            results = await discovery.search_by_keywords(kw, limit=min(limit, 50))
            results = await discovery.filter_open_comments(results)

        elif parser_type == "users":
            from src.services.channel_discovery import ChannelDiscovery

            discovery = ChannelDiscovery(telegram)
            kw = [target] if keywords is None else [k.strip() for k in keywords.split(",") if k.strip()]
            results = await discovery.search_by_keywords(kw, limit=min(limit, 50))

        elif parser_type == "messages":
            messages = await telegram.parse_last_messages(target, limit=min(limit, 20))
            results = [
                {
                    "username": target,
                    "title": target,
                    "members": 0,
                    "has_comments": False,
                    "message_id": m.get("id"),
                    "text": m.get("text", "")[:200],
                    "date": m.get("date", ""),
                    "views": m.get("views", 0),
                }
                for m in messages
            ]

        _update_task(task_id, "completed", results)
        logger.info(f"[{task_id}] Parsing complete: {len(results)} results")
    except Exception as e:
        logger.error(f"[{task_id}] Parsing error: {e}")
        _update_task(task_id, "failed", [], str(e))
    finally:
        await telegram.disconnect()

    return results


def _update_task(task_id: str, status: str, results: list, error: Optional[str] = None):
    tasks_db = "data/tasks.db"
    os.makedirs("data", exist_ok=True)
    with sqlite3.connect(tasks_db) as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY, type TEXT, status TEXT,
                params TEXT, created_at TEXT, completed_at TEXT, results TEXT, error TEXT
            )"""
        )
        conn.execute(
            "UPDATE tasks SET status = ?, completed_at = ?, results = ?, error = ? WHERE task_id = ?",
            (status, datetime.now().isoformat(), json.dumps(results), error, task_id),
        )
        conn.commit()
