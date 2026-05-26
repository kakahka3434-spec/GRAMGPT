from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from src.celery_app import celery_app
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


@router.post("/parsing/start")
async def start_parsing(req: ParseRequest):
    from src.config import settings
    if not all([settings.telegram_api_id, settings.telegram_api_hash]):
        raise HTTPException(status_code=503, detail="Telegram credentials not configured")

    task_id = f"parse_{uuid.uuid4().hex[:8]}_{int(datetime.now().timestamp())}"
    tasks_db = "data/tasks.db"
    os.makedirs("data", exist_ok=True)
    with sqlite3.connect(tasks_db) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY, type TEXT, status TEXT,
                params TEXT, created_at TEXT, completed_at TEXT, results TEXT
            )
        """)
        conn.execute(
            "INSERT INTO tasks VALUES (?, ?, ?, ?, ?, ?, ?)",
            (task_id, req.parser_type, "processing", json.dumps(req.dict()),
             datetime.now().isoformat(), None, None)
        )
        conn.commit()

    celery_app.send_task("run_parsing_task", args=[req.parser_type, req.target, req.keywords, req.limit],
                         task_id=task_id)

    return {"status": "processing", "task_id": task_id, "parser_type": req.parser_type, "target": req.target}


@router.get("/parsing/results/{task_id}")
async def get_parsing_results(task_id: str):
    tasks_db = "data/tasks.db"
    if not os.path.exists(tasks_db):
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    with sqlite3.connect(tasks_db) as conn:
        cursor = conn.execute("SELECT status, results FROM tasks WHERE task_id = ?", (task_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        status, results_json = row
        if status == "processing":
            return {"task_id": task_id, "status": "processing", "message": "Task is still running"}
        results = json.loads(results_json) if results_json else []
        return {"task_id": task_id, "status": status, "total_found": len(results), "results": results[:100]}
