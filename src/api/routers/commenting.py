import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from src.celery_app import celery_app

router = APIRouter(prefix="/api/v1", tags=["commenting"])


class CommentingConfig(BaseModel):
    channels: List[str]
    tone: str = "expert"
    model: str = "gpt-4o"
    frequency: str = "every_2nd"


class ChattingConfig(BaseModel):
    groups: List[str]
    strategy: str = "expert"
    max_per_hour: int = 10
    delay: str = "2-5min"


class ReactionsConfig(BaseModel):
    channels: List[str]
    emojis: List[str] = ["👍", "❤️", "🔥", "🚀"]
    mapping: str = "ai"
    per_post: str = "50-200"
    delay: str = "1-5s"


def _redis_available():
    try:
        import socket
        s = socket.create_connection(("localhost", 6379), timeout=0.5)
        s.close()
        return True
    except Exception:
        return False


@router.post("/commenting/start")
async def start_commenting(config: CommentingConfig):
    if _redis_available():
        celery_app.send_task("run_commenting_task", args=[config.channels, config.tone, config.model])
    else:
        asyncio.create_task(_run_commenting_inline(config.channels, config.tone, config.model))

    return {
        "session_id": f"celery_{config.channels[0] if config.channels else 'unknown'}",
        "status": "queued",
        "channels": config.channels,
        "tone": config.tone,
        "model": config.model,
        "mode": "celery" if _redis_available() else "inline",
    }


async def _run_commenting_inline(channels: list, tone: str, model: str):
    from src.services.telegram_user_client import TelegramUserClient
    from src.services.comment_sender import CommentSender
    from src.config import settings

    telegram = TelegramUserClient(
        api_id=settings.telegram_api_id,
        api_hash=settings.telegram_api_hash,
        phone=settings.telegram_phone,
        session_path="data/sessions/gramgpt_user",
    )
    try:
        connected = await asyncio.wait_for(telegram.connect(), timeout=30.0)
        if not connected:
            return
        sender = CommentSender(telegram)
        for ch in channels[:5]:
            posts = await telegram.parse_last_messages(ch, limit=3)
            if not posts:
                continue
            await sender.batch_comment(channel=ch, posts=posts, style=tone, max_comments=2)
    finally:
        await telegram.disconnect()


@router.get("/commenting/logs")
async def get_commenting_logs():
    try:
        from src.db.comment_memory import CommentMemory
        mem = CommentMemory()
        posts = mem.get_all_recent(hours=72)
        return [
            {
                "channel": p.get("channel", ""),
                "comment": p.get("text", ""),
                "likes": 0,
                "replies": 0,
                "time": p.get("timestamp", ""),
            }
            for p in posts
        ]
    except Exception:
        return []


@router.post("/chatting/start")
async def start_chatting(config: ChattingConfig):
    if _redis_available():
        celery_app.send_task("run_chatting_task", args=[config.groups, config.strategy, config.max_per_hour])
    else:
        asyncio.create_task(_run_chatting_inline(config.groups, config.strategy))
    return {"status": "queued", "groups": config.groups, "strategy": config.strategy, "mode": "celery" if _redis_available() else "inline"}


async def _run_chatting_inline(groups: list, strategy: str):
    from src.services.telegram_user_client import TelegramUserClient
    from src.config import settings
    telegram = TelegramUserClient(api_id=settings.telegram_api_id, api_hash=settings.telegram_api_hash, phone=settings.telegram_phone, session_path="data/sessions/gramgpt_user")
    connected = await asyncio.wait_for(telegram.connect(), timeout=30.0)
    if not connected:
        return
    try:
        results = []
        for group in groups[:5]:
            sent = await telegram.send_comment(group, f"Chatting in {group} (strategy: {strategy})")
            results.append({"group": group, "sent": bool(sent)})
    finally:
        await telegram.disconnect()


@router.get("/dialogs/active")
async def get_active_dialogs():
    try:
        import sqlite3, os
        BASE = os.path.join(os.path.dirname(__file__), "..", "..", "..", "gramgpt.db")
        conn = sqlite3.connect(BASE)
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM leads ORDER BY last_contact DESC LIMIT 10").fetchall()
        conn.close()
        dialogs = []
        for r in rows:
            stage = r["status"] or "new"
            dialogs.append({
                "name": r["username"] or f"User #{r['tg_id']}",
                "stage": "hot" if stage == "hot" else "warm" if stage in ("in_progress",) else "cold",
                "last_msg": str(r.get("last_contact", "")),
                "status": "active" if stage != "closed" else "new",
            })
        return {"total_active": len(dialogs), "conversion_rate": 0, "leads": len(dialogs), "dialogs": dialogs}
    except Exception:
        return {"total_active": 0, "conversion_rate": 0, "leads": 0, "dialogs": []}


@router.post("/dialogs/start")
async def start_dialogs():
    if _redis_available():
        celery_app.send_task("run_dialogs_task")
    return {"status": "queued", "ai_mode": "auto", "funnel_steps": 4, "mode": "celery" if _redis_available() else "inline"}


@router.post("/reactions/start")
async def start_reactions(config: ReactionsConfig):
    if _redis_available():
        celery_app.send_task("run_reactions_task", args=[config.channels, config.emojis])
    return {"status": "queued", "channels": config.channels, "emojis": config.emojis, "mode": "celery" if _redis_available() else "inline"}


@router.get("/reactions/stats")
async def get_reactions_stats():
    try:
        from src.core.account_pool import AccountPool
        pool = AccountPool()
        accounts = pool.list_accounts()
        total = sum(a.get("success_count", 0) for a in accounts)
        return {"total": total, "today": 0, "channels": len(accounts)}
    except Exception:
        return {"total": 0, "today": 0, "channels": 0}


@router.get("/warmup/accounts")
async def get_warmup_accounts():
    try:
        from src.core.account_pool import AccountPool
        pool = AccountPool()
        accounts = pool.list_accounts()
        return [
            {
                "phone": a.get("phone", f"+{a.get('id', 0)}"),
                "trust": a.get("trust_score", 50),
                "status": a.get("status", "idle"),
                "dialogs": a.get("success_count", 0),
            }
            for a in accounts
        ]
    except Exception:
        return []


@router.post("/warmup/start")
async def start_warmup():
    if _redis_available():
        celery_app.send_task("run_account_check_task")
    return {"status": "queued", "anti_ban": True, "human_emulation": True, "mode": "celery" if _redis_available() else "inline"}
