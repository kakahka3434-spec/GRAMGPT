from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from src.celery_app import celery_app
from src.config import settings
import os
import sqlite3
import json
import uuid
from datetime import datetime

router = APIRouter(prefix="/api/v1", tags=["parsing"])


class ParseRequest(BaseModel):
    parser_type: str
    target: str
    keywords: Optional[str] = None
    limit: int = 1000
    period: str = "7d"


def _init_tasks_db():
    os.makedirs("data", exist_ok=True)
    with sqlite3.connect("data/tasks.db") as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY, type TEXT, status TEXT,
                params TEXT, created_at TEXT, completed_at TEXT, results TEXT, error TEXT
            )
        """)
        conn.commit()


def _create_task(task_id: str, parser_type: str, params: dict):
    _init_tasks_db()
    with sqlite3.connect("data/tasks.db") as conn:
        conn.execute(
            "INSERT INTO tasks (task_id, type, status, params, created_at) VALUES (?, ?, ?, ?, ?)",
            (task_id, parser_type, "processing", json.dumps(params), datetime.now().isoformat()),
        )
        conn.commit()


@router.post("/parsing/start")
async def start_parsing(req: ParseRequest):
    if not all([settings.telegram_api_id, settings.telegram_api_hash, settings.telegram_phone]):
        raise HTTPException(
            status_code=503,
            detail="Telegram credentials not configured. Set TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE in .env.local"
        )

    task_id = f"parse_{uuid.uuid4().hex[:8]}_{int(datetime.now().timestamp())}"
    _create_task(task_id, req.parser_type, req.model_dump())

    redis_available = False
    try:
        import socket
        s = socket.create_connection(("localhost", 6379), timeout=0.5)
        s.close()
        redis_available = True
    except Exception:
        pass

    if not redis_available:
        raise HTTPException(status_code=503, detail="Redis unavailable. Celery required for parsing tasks.")

    celery_app.send_task(
        "run_parsing_task",
        args=[req.parser_type, req.target, req.keywords, req.limit],
        task_id=task_id,
    )

    return {
        "status": "processing",
        "task_id": task_id,
        "parser_type": req.parser_type,
        "target": req.target,
        "mode": "celery",
    }


@router.get("/parsing/results/{task_id}")
async def get_parsing_results(task_id: str):
    if not os.path.exists("data/tasks.db"):
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    with sqlite3.connect("data/tasks.db") as conn:
        cursor = conn.execute("SELECT status, results, error FROM tasks WHERE task_id = ?", (task_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        status, results_json, error = row

        if status == "processing":
            return {"task_id": task_id, "status": "processing", "message": "Task is still running"}

        if status == "failed":
            return {"task_id": task_id, "status": "failed", "error": error, "results": []}

        results = json.loads(results_json) if results_json else []
        return {"task_id": task_id, "status": status, "total_found": len(results), "results": results[:100]}
