"""System health endpoint — shows status of all services."""

from fastapi import APIRouter
import os, socket, sqlite3

router = APIRouter(prefix="/api/v1", tags=["system"])


def _check_port(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        s = socket.create_connection((host, port), timeout=timeout)
        s.close()
        return True
    except Exception:
        return False


def _check_sqlite(path: str) -> dict:
    try:
        conn = sqlite3.connect(path)
        conn.execute("SELECT 1")
        conn.close()
        size = os.path.getsize(path) if os.path.exists(path) else 0
        return {"ok": True, "size_kb": round(size / 1024, 1)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/health")
async def system_health():
    from src.config import settings

    # Redis
    redis_ok = _check_port("localhost", 6379)

    # Telegram credentials
    tg_creds = all([settings.telegram_api_id, settings.telegram_api_hash])
    tg_phone = bool(settings.telegram_phone)

    # AI provider
    ai_keys = {
        "openai": bool(settings.openai_api_key),
        "openrouter": bool(settings.openrouter_api_key),
        "groq": bool(settings.groq_api_key),
    }
    ai_configured = any(ai_keys.values())

    # SQLite databases
    gramgpt_db = _check_sqlite("gramgpt.db")
    tasks_db = _check_sqlite("data/tasks.db") if os.path.exists("data/tasks.db") else {"ok": False, "error": "not yet created"}
    incidents_db = _check_sqlite("data/incidents.db") if os.path.exists("data/incidents.db") else {"ok": False, "error": "not yet created"}

    return {
        "status": "ok",
        "services": {
            "redis": {
                "available": redis_ok,
                "mode": "distributed_queue" if redis_ok else "eager_inline_fallback",
                "note": "Install Redis for production: https://redis.io/download" if not redis_ok else None,
            },
            "telegram": {
                "credentials_configured": tg_creds,
                "phone_configured": tg_phone,
            },
            "ai_provider": {
                "provider": settings.ai_provider,
                "keys_configured": ai_keys,
                "active": ai_configured,
            },
            "database": {
                "gramgpt.db": gramgpt_db,
                "data/tasks.db": tasks_db,
                "data/incidents.db": incidents_db,
            },
        },
        "version": "2.0",
    }
