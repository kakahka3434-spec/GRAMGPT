import asyncio
import json
import logging
import os
import sqlite3
import aiohttp
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


class AutomationEngine:
    """
    Rules-based automation engine with triggers, conditions, actions,
    webhook support, and retry logic.
    """

    def __init__(self, db_path: str = "data/automation.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self._init_db()
        self._handlers: Dict[str, List[Callable]] = {}

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    trigger_type TEXT NOT NULL,
                    conditions TEXT,
                    actions TEXT NOT NULL,
                    enabled INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT (datetime('now')),
                    last_triggered TEXT
                );
                CREATE TABLE IF NOT EXISTS triggers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_id INTEGER,
                    event_type TEXT NOT NULL,
                    event_data TEXT,
                            triggered_at TEXT DEFAULT (datetime('now')),
                    result TEXT,
                    status TEXT DEFAULT 'pending',
                    retry_count INTEGER DEFAULT 0,
                    FOREIGN KEY (rule_id) REFERENCES rules(id)
                );
                CREATE TABLE IF NOT EXISTS webhook_configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    url TEXT NOT NULL,
                    headers TEXT,
                    retry_count INTEGER DEFAULT 3,
                    timeout INTEGER DEFAULT 30,
                    enabled INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT (datetime('now'))
                );
            """)

    async def create_rule(self, name: str, trigger_type: str, conditions: List[Dict], actions: List[Dict]) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "INSERT INTO rules (name, trigger_type, conditions, actions) VALUES (?, ?, ?, ?)",
                (name, trigger_type, json.dumps(conditions), json.dumps(actions)),
            )
            conn.commit()
            rule_id = cur.lastrowid
        logger.info(f"Created automation rule #{rule_id}: {name}")
        return rule_id

    async def evaluate_rule(self, rule_id: int, event_type: str, event_data: Dict) -> Optional[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM rules WHERE id=? AND enabled=1", (rule_id,)).fetchone()
            if not row:
                return None

        conditions = json.loads(row["conditions"]) if isinstance(row["conditions"], str) else []
        if not self._check_conditions(conditions, event_data):
            return None

        actions = json.loads(row["actions"]) if isinstance(row["actions"], str) else []
        results = []
        for action in actions:
            result = await self._execute_action(action, event_data)
            results.append(result)

        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO triggers (rule_id, event_type, event_data, result, status) VALUES (?, ?, ?, ?, 'completed')",
            (rule_id, event_type, json.dumps(event_data), json.dumps(results)),
        )
        conn.execute("UPDATE rules SET last_triggered=datetime('now') WHERE id=?", (rule_id,))
        conn.commit()
        conn.close()

        return {"rule_id": rule_id, "results": results}

    def _check_conditions(self, conditions: List[Dict], event_data: Dict) -> bool:
        for cond in conditions:
            field = cond.get("field", "")
            operator = cond.get("operator", "eq")
            value = cond.get("value")
            actual = event_data.get(field)
            if operator == "eq" and actual != value:
                return False
            elif operator == "gt" and not (actual and actual > value):
                return False
            elif operator == "lt" and not (actual and actual < value):
                return False
            elif operator == "contains" and not (actual and value in str(actual)):
                return False
        return True

    async def _execute_action(self, action: Dict, event_data: Dict) -> Dict:
        action_type = action.get("type", "")
        params = action.get("params", {})

        if action_type == "webhook":
            return await self.trigger_webhook(params.get("url", ""), {"event": event_data, **params})
        elif action_type == "pause_account":
            phone = params.get("phone", event_data.get("phone", ""))
            if phone:
                from src.core.account_pool import AccountPool
                pool = AccountPool()
                pool.mark_status(phone, "cooldown", cooldown_minutes=int(params.get("minutes", 60)))
                return {"action": "pause_account", "phone": phone, "minutes": params.get("minutes", 60)}
        elif action_type == "notify":
            logger.info(f"NOTIFICATION: {params.get('message', '')}")
            return {"action": "notify", "message": params.get("message", "")}
        elif action_type == "change_mode":
            from src.core.work_modes import work_mode_controller
            mode = params.get("mode", "safe")
            work_mode_controller.set_override(mode)
            return {"action": "change_mode", "mode": mode}

        return {"action": action_type, "status": "unknown_type"}

    async def trigger_webhook(self, url: str, payload: Dict[str, Any], retries: int = 3, timeout: int = 30) -> Dict:
        for attempt in range(retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
                        data = await resp.json()
                        logger.info(f"Webhook {url} responded {resp.status}")
                        return {"status": "sent", "code": resp.status, "response": data}
            except asyncio.TimeoutError:
                logger.warning(f"Webhook {url} timed out (attempt {attempt + 1}/{retries})")
            except Exception as e:
                logger.warning(f"Webhook {url} failed (attempt {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                await asyncio.sleep(2 ** attempt)
        return {"status": "failed", "error": f"All {retries} retries exhausted"}

    def on(self, event_type: str, handler: Callable):
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    async def emit(self, event_type: str, data: Dict):
        """Emit an event to all matching rules and handlers."""
        for handler in self._handlers.get(event_type, []):
            try:
                await handler(data)
            except Exception as e:
                logger.error(f"Handler for {event_type} failed: {e}")

        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT id FROM rules WHERE trigger_type=? AND enabled=1", (event_type,)
            ).fetchall()

        for (rule_id,) in rows:
            await self.evaluate_rule(rule_id, event_type, data)

    def list_rules(self) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            return [dict(r) for r in conn.execute("SELECT * FROM rules ORDER BY id DESC").fetchall()]

    def list_triggers(self, limit: int = 50) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            return [dict(r) for r in conn.execute("SELECT * FROM triggers ORDER BY triggered_at DESC LIMIT ?", (limit,)).fetchall()]

    def list_webhooks(self) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            return [dict(r) for r in conn.execute("SELECT * FROM webhook_configs ORDER BY id DESC").fetchall()]

    async def add_webhook_config(self, name: str, url: str, headers: Optional[Dict] = None, retries: int = 3) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "INSERT INTO webhook_configs (name, url, headers, retry_count) VALUES (?, ?, ?, ?)",
                (name, url, json.dumps(headers or {}), retries),
            )
            conn.commit()
            return cur.lastrowid

    def get_stats(self) -> Dict:
        with sqlite3.connect(self.db_path) as conn:
            total_rules = conn.execute("SELECT COUNT(*) FROM rules").fetchone()[0]
            enabled_rules = conn.execute("SELECT COUNT(*) FROM rules WHERE enabled=1").fetchone()[0]
            total_triggers = conn.execute("SELECT COUNT(*) FROM triggers").fetchone()[0]
            failed = conn.execute("SELECT COUNT(*) FROM triggers WHERE status='failed'").fetchone()[0]
        return {
            "total_rules": total_rules,
            "enabled_rules": enabled_rules,
            "total_triggers": total_triggers,
            "failed_triggers": failed,
        }


automation = AutomationEngine()
