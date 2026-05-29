import asyncio
import json
import logging
import os
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from src.core.ai_client import ai_client

logger = logging.getLogger(__name__)


class AICrisisManager:
    """
    Real-time crisis detection and response system.
    Monitors account health, detects anomalies, and auto-escalates.
    """

    def __init__(self, db_path: str = "data/crisis.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self._init_db()
        self.report_threshold = 5
        self.monitoring_interval = 300
        self._monitor_task: Optional[asyncio.Task] = None

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS incidents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id TEXT NOT NULL,
                    incident_type TEXT NOT NULL,
                    details TEXT,
                    severity INTEGER DEFAULT 1,
                    status TEXT DEFAULT 'open',
                    reported_at TEXT DEFAULT (datetime('now')),
                    resolved_at TEXT,
                    resolution TEXT
                );
                CREATE TABLE IF NOT EXISTS crisis_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    incident_id INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    result TEXT,
                    executed_at TEXT,
                    FOREIGN KEY (incident_id) REFERENCES incidents(id)
                );
                CREATE TABLE IF NOT EXISTS account_health (
                    phone TEXT PRIMARY KEY,
                    risk_score INTEGER DEFAULT 0,
                    last_check TEXT,
                    is_paused INTEGER DEFAULT 0,
                    pause_until TEXT,
                    consecutive_errors INTEGER DEFAULT 0,
                    total_incidents_24h INTEGER DEFAULT 0
                );
            """)

    async def record_incident(self, account_id: str, incident_type: str, details: Optional[str] = None,
                              severity: int = 1) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "INSERT INTO incidents (account_id, incident_type, details, severity) VALUES (?, ?, ?, ?)",
                (account_id, incident_type, details, severity),
            )
            conn.commit()
            incident_id = cur.lastrowid
        logger.warning(f"Incident #{incident_id}: {incident_type} on {account_id} (sev={severity})")
        return incident_id

    async def detect_crisis(self, account_id: str, current_reports: int) -> Optional[Dict]:
        report_24h = self._count_incidents_24h(account_id)
        total_severity = self._total_severity_24h(account_id)

        if report_24h >= self.report_threshold or total_severity >= 10:
            logger.warning(f"CRISIS DETECTED for {account_id}! Reports={report_24h}, Severity={total_severity}")
            return await self._escalate(account_id, f"High report volume ({report_24h} in 24h)")

        if current_reports >= self.report_threshold:
            return await self._escalate(account_id, f"Current reports threshold ({current_reports})")

        return None

    def _count_incidents_24h(self, account_id: str) -> int:
        try:
            with sqlite3.connect(self.db_path) as conn:
                row = conn.execute(
                    "SELECT COUNT(*) FROM incidents WHERE account_id=? AND reported_at > datetime('now', '-1 day')",
                    (account_id,),
                ).fetchone()
                return row[0] if row else 0
        except Exception:
            return 0

    def _total_severity_24h(self, account_id: str) -> int:
        try:
            with sqlite3.connect(self.db_path) as conn:
                row = conn.execute(
                    "SELECT COALESCE(SUM(severity), 0) FROM incidents WHERE account_id=? AND reported_at > datetime('now', '-1 day')",
                    (account_id,),
                ).fetchone()
                return row[0] if row else 0
        except Exception:
            return 0

    async def _escalate(self, account_id: str, reason: str) -> Dict:
        prompt = (
            f"CRISIS: Account {account_id}\n"
            f"Reason: {reason}\n\n"
            "Analyze the situation and recommend 3 actions ranked by effectiveness. "
            "Return JSON with: analysis (string), actions (array of {name, description, risk_level, cooldown_hours})"
        )
        try:
            resp = await ai_client.get_chat_response(0, [{"role": "user", "content": prompt}])
            try:
                start = resp.index("{")
                end = resp.rindex("}") + 1
                analysis = json.loads(resp[start:end])
            except (ValueError, json.JSONDecodeError):
                analysis = {"analysis": resp, "actions": []}
        except Exception:
            analysis = {"analysis": "Unable to generate AI analysis", "actions": []}

        actions = analysis.get("actions", []) or [
            {"name": "Смена IP", "description": "Пауза 48 часов + смена прокси", "risk_level": "low", "cooldown_hours": 48},
            {"name": "Масс-реакции", "description": "Удаление последних сообщений + активность на белых каналах", "risk_level": "medium", "cooldown_hours": 24},
            {"name": "Мимикрия", "description": "Поведение как личный аккаунт (сторис, переписки)", "risk_level": "high", "cooldown_hours": 72},
        ]

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO account_health (phone, risk_score, last_check, is_paused, total_incidents_24h) VALUES (?, ?, datetime('now'), 1, ?)",
                (account_id, min(100, self._total_severity_24h(account_id) * 10), self._count_incidents_24h(account_id)),
            )
            conn.commit()

        return {
            "account_id": account_id,
            "status": "paused",
            "analysis": analysis.get("analysis", reason),
            "actions": actions,
        }

    async def check_account_health(self, phone: str, error_count: int = 0, success_count: int = 0) -> Dict:
        """Periodic health check with auto-escalation."""
        risk = min(100, error_count * 15 - success_count * 2 + self._total_severity_24h(phone) * 5)
        risk = max(0, risk)

        with sqlite3.connect(self.db_path) as conn:
            existing = conn.execute("SELECT * FROM account_health WHERE phone=?", (phone,)).fetchone()
            if existing and existing[4]:  # is_paused
                pause_until = existing[5]
                if pause_until and datetime.fromisoformat(pause_until) > datetime.now():
                    return {"phone": phone, "risk": risk, "status": "paused", "pause_until": pause_until}

            conn.execute(
                "INSERT OR REPLACE INTO account_health (phone, risk_score, last_check, consecutive_errors) VALUES (?, ?, datetime('now'), ?)",
                (phone, risk, error_count),
            )
            conn.commit()

        status = "safe" if risk < 30 else "warning" if risk < 60 else "danger" if risk < 85 else "critical"

        if status in ("danger", "critical"):
            from src.core.account_pool import AccountPool
            pool = AccountPool()
            pool.mark_status(phone, "cooldown", cooldown_minutes=120)
            await self.record_incident(phone, "high_risk", f"Risk score: {risk}", severity=3)

            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "UPDATE account_health SET is_paused=1, pause_until=datetime('now', '+2 hours') WHERE phone=?",
                    (phone,),
                )
                conn.commit()

        return {"phone": phone, "risk": risk, "status": status}

    def get_active_crises(self) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            return [dict(r) for r in conn.execute(
                "SELECT * FROM incidents WHERE status='open' ORDER BY severity DESC, reported_at DESC LIMIT 20"
            ).fetchall()]

    def get_account_health(self, phone: Optional[str] = None) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if phone:
                return [dict(r) for r in conn.execute("SELECT * FROM account_health WHERE phone=?", (phone,)).fetchall()]
            return [dict(r) for r in conn.execute("SELECT * FROM account_health ORDER BY risk_score DESC").fetchall()]

    def resolve_incident(self, incident_id: int, resolution: str = "manual"):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE incidents SET status='resolved', resolved_at=datetime('now'), resolution=? WHERE id=?",
                (resolution, incident_id),
            )
            conn.commit()

    def start_monitoring(self):
        if self._monitor_task:
            return
        self._monitor_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Crisis monitoring started")

    def stop_monitoring(self):
        if self._monitor_task:
            self._monitor_task.cancel()
            self._monitor_task = None
            logger.info("Crisis monitoring stopped")

    async def _monitoring_loop(self):
        while True:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    at_risk = conn.execute(
                        "SELECT * FROM account_health WHERE is_paused=0 AND risk_score > 50"
                    ).fetchall()

                for acc in at_risk:
                    await self.escalate(acc["phone"], f"Risk score {acc['risk_score']} exceeded threshold")

                await asyncio.sleep(self.monitoring_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(60)


crisis_manager = AICrisisManager()
