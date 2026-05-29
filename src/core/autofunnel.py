import asyncio
import json
import logging
import os
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from src.core.human_emulation import human_engine
from src.core.router import channel_router, Channel

logger = logging.getLogger(__name__)


class AutoFunnelEngine:
    def __init__(self, db_path: str = "data/funnel.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self._init_db()
        self.active_funnels: Dict[int, asyncio.Task] = {}

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS funnels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lead_id INTEGER NOT NULL,
                    name TEXT DEFAULT '',
                    stage TEXT DEFAULT 'parsing',
                    status TEXT DEFAULT 'active',
                    config TEXT,
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now')),
                    completed_at TEXT
                );
                CREATE TABLE IF NOT EXISTS funnel_stages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    funnel_id INTEGER NOT NULL,
                    stage TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    delay_days REAL DEFAULT 0,
                    result TEXT,
                    started_at TEXT,
                    completed_at TEXT,
                    FOREIGN KEY (funnel_id) REFERENCES funnels(id)
                );
                CREATE TABLE IF NOT EXISTS funnel_leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    funnel_id INTEGER NOT NULL,
                    phone TEXT,
                    username TEXT,
                    status TEXT DEFAULT 'new',
                    stage_reached TEXT DEFAULT '',
                    interaction_count INTEGER DEFAULT 0,
                    last_contact TEXT,
                    created_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (funnel_id) REFERENCES funnels(id)
                );
            """)

    async def create_funnel(self, name: str, goal: str, stages_config: Optional[List[Dict]] = None) -> int:
        if stages_config is None:
            stages_config = [
                {"stage": "parsing", "delay_days": 0},
                {"stage": "warmup", "delay_days": 1},
                {"stage": "commenting", "delay_days": 2},
                {"stage": "dm_outreach", "delay_days": 3},
                {"stage": "story_reaction", "delay_days": 5},
                {"stage": "final_push", "delay_days": 7},
            ]
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "INSERT INTO funnels (lead_id, name, config, stage, status) VALUES (?, ?, ?, ?, 'active')",
                (0, name, json.dumps(stages_config), "parsing"),
            )
            funnel_id = cur.lastrowid
            for i, s in enumerate(stages_config):
                conn.execute(
                    "INSERT INTO funnel_stages (funnel_id, stage, delay_days, status) VALUES (?, ?, ?, 'pending')",
                    (funnel_id, s["stage"], s.get("delay_days", 0)),
                )
            conn.commit()
        logger.info(f"Created funnel #{funnel_id}: {name}")
        return funnel_id

    async def execute_sequence(self, lead_id: int, sequence_config: List[Dict]):
        logger.info(f"Starting AutoFunnel for lead {lead_id}")
        for step in sequence_config:
            stage = step.get("stage")
            delay_days = step.get("delay_days", 0)
            if delay_days > 0:
                logger.info(f"Lead {lead_id}: Waiting {delay_days}d for stage {stage}")
                await asyncio.sleep(delay_days * 86400)
            await self._run_stage(lead_id, stage, step.get("data") or {})

    async def _run_stage(self, lead_id: int, stage: str, data: Dict):
        logger.info(f"Lead {lead_id}: Executing stage {stage}")
        if stage == "parsing":
            from src.services.parser_service import run_parsing
            target = data.get("target", "")
            keywords = data.get("keywords", "")
            if target:
                results = await run_parsing("task_stub", "keywords", target, keywords, 100)
                return {"parsed": len(results) if results else 0}
        elif stage == "warmup":
            from src.core.account_pool import AccountPool
            pool = AccountPool()
            accounts = pool.list_accounts()
            for acc in accounts[:3]:
                logger.info(f"Warming account {acc.get('phone')} for lead {lead_id}")
            return {"warmed": min(3, len(accounts))}
        elif stage == "commenting":
            from src.services.comment_sender import CommentSender
            from src.services.telegram_user_client import TelegramUserClient
            client = TelegramUserClient()
            sender = CommentSender(client)
            channel = data.get("channel", "")
            if channel:
                await sender.send_comment(channel, data.get("text", "Great post!"))
                return {"commented": 1}
        elif stage == "dm_outreach":
            text = data.get("text", "Hi! Interested in our offer?")
            await channel_router.route_lead(lead_id, Channel.TELEGRAM, text)
            return {"dm_sent": 1}
        elif stage == "story_reaction":
            return {"reacted": 1}
        elif stage == "final_push":
            text = data.get("text", "Reminder: Special offer expires soon!")
            await channel_router.route_lead(lead_id, Channel.WHATSAPP, text)
            return {"push_sent": 1}
        return {"stage": stage, "status": "done"}

    async def run_funnel_background(self, funnel_id: int):
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT * FROM funnels WHERE id=?", (funnel_id,)).fetchone()
            if not row:
                return
            config = json.loads(row[4]) if isinstance(row[4], str) else []
        for stage_cfg in config:
            stage_name = stage_cfg.get("stage", "")
            delay_days = stage_cfg.get("delay_days", 0)
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "UPDATE funnel_stages SET status='running', started_at=datetime('now') WHERE funnel_id=? AND stage=?",
                    (funnel_id, stage_name),
                )
                conn.execute("UPDATE funnels SET stage=?, updated_at=datetime('now') WHERE id=?", (stage_name, funnel_id))
                conn.commit()
            if delay_days > 0:
                await asyncio.sleep(delay_days * 86400)
            result = await self._run_stage(funnel_id, stage_name, {})
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "UPDATE funnel_stages SET status='completed', result=?, completed_at=datetime('now') WHERE funnel_id=? AND stage=?",
                    (json.dumps(result), funnel_id, stage_name),
                )
                conn.commit()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE funnels SET status='completed', completed_at=datetime('now') WHERE id=?",
                (funnel_id,),
            )
            conn.commit()
        self.active_funnels.pop(funnel_id, None)

    async def start_funnel(self, funnel_id: int):
        if funnel_id in self.active_funnels:
            return
        task = asyncio.create_task(self.run_funnel_background(funnel_id))
        self.active_funnels[funnel_id] = task
        logger.info(f"Funnel #{funnel_id} started in background")

    def get_funnel_status(self, funnel_id: int) -> Optional[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM funnels WHERE id=?", (funnel_id,)).fetchone()
            if not row:
                return None
            stages = conn.execute("SELECT * FROM funnel_stages WHERE funnel_id=? ORDER BY id", (funnel_id,)).fetchall()
            return {
                "id": row["id"],
                "name": row["name"],
                "stage": row["stage"],
                "status": row["status"],
                "created_at": row["created_at"],
                "completed_at": row["completed_at"],
                "stages": [dict(s) for s in stages],
            }

    def list_funnels(self) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            return [dict(r) for r in conn.execute("SELECT * FROM funnels ORDER BY id DESC").fetchall()]

    def stop_funnel(self, funnel_id: int):
        task = self.active_funnels.pop(funnel_id, None)
        if task:
            task.cancel()
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("UPDATE funnels SET status='cancelled' WHERE id=?", (funnel_id,))
                conn.commit()
            logger.info(f"Funnel #{funnel_id} cancelled")


autofunnel = AutoFunnelEngine()
