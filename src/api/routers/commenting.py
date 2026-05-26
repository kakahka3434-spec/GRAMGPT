from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
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


@router.post("/commenting/start")
async def start_commenting(config: CommentingConfig):
    celery_app.send_task("run_commenting_task", args=[config.channels, config.tone, config.model])
    return {
        "session_id": f"celery_{config.channels[0] if config.channels else 'unknown'}",
        "status": "queued",
        "channels": config.channels,
        "tone": config.tone,
        "model": config.model,
    }


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
    celery_app.send_task("run_commenting_task", args=[config.groups, config.strategy])
    return {"status": "queued", "groups": config.groups, "strategy": config.strategy}


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
    celery_app.send_task("run_commenting_task")
    return {"status": "queued", "ai_mode": "auto", "funnel_steps": 4}


@router.post("/reactions/start")
async def start_reactions(config: ReactionsConfig):
    celery_app.send_task("run_commenting_task", args=[config.channels, config.emojis])
    return {"status": "queued", "channels": config.channels, "emojis": config.emojis}


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
    celery_app.send_task("run_account_check_task")
    return {"status": "queued", "anti_ban": True, "human_emulation": True}
