import json
import logging
import os
import sqlite3
import aiohttp
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class CRMSync:
    """
    Real CRM sync engine with webhook delivery, retry logic,
    and sync history tracking.
    """

    def __init__(self, db_path: str = "data/crm_sync.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self._init_db()
        self.webhooks: List[Dict] = []

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS sync_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT NOT NULL,
                    lead_phone TEXT,
                    lead_username TEXT,
                    status TEXT DEFAULT 'pending',
                    payload TEXT,
                    response TEXT,
                    created_at TEXT DEFAULT (datetime('now')),
                    synced_at TEXT
                );
                CREATE TABLE IF NOT EXISTS webhook_targets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT NOT NULL,
                    url TEXT NOT NULL,
                    api_key TEXT,
                    enabled INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT (datetime('now'))
                );
            """)

    async def sync_lead(self, lead_data: Dict[str, Any], platform: str = "amoCRM") -> Dict:
        phone = lead_data.get("phone", lead_data.get("tg_id", ""))
        username = lead_data.get("username", "")

        payload = {
            "name": username or f"User {phone}",
            "phone": phone,
            "status": "new_lead",
            "source": "GRAMGPT",
            "tags": lead_data.get("tags", ["telegram"]),
            "custom_fields": {
                "tg_id": lead_data.get("tg_id", ""),
                "last_contact": lead_data.get("last_contact", ""),
                "interest": lead_data.get("interest", ""),
            },
            "timestamp": datetime.now().isoformat(),
        }

        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "INSERT INTO sync_log (platform, lead_phone, lead_username, payload) VALUES (?, ?, ?, ?)",
                (platform, phone, username, json.dumps(payload)),
            )
            log_id = cur.lastrowid
            conn.commit()

        result = await self._deliver(platform, payload)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE sync_log SET status=?, response=?, synced_at=datetime('now') WHERE id=?",
                (result.get("status", "error"), json.dumps(result), log_id),
            )
            conn.commit()

        return {"status": result.get("status", "synced"), "platform": platform, "log_id": log_id}

    async def _deliver(self, platform: str, payload: Dict) -> Dict:
        target = self._get_target(platform)
        if not target:
            for webhook in self.webhooks:
                if webhook.get("platform", "").lower() == platform.lower():
                    target = webhook
                    break
        if not target:
            logger.info(f"No webhook for {platform}, logging only")
            return {"status": "logged"}

        url = target["url"]
        headers = {"Content-Type": "application/json"}
        if target.get("api_key"):
            headers["Authorization"] = f"Bearer {target['api_key']}"

        for attempt in range(3):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=payload, headers=headers,
                                            timeout=aiohttp.ClientTimeout(total=15)) as resp:
                        body = await resp.text()
                        if resp.ok:
                            logger.info(f"CRM {platform} synced ({resp.status})")
                            return {"status": "synced", "code": resp.status, "response": body[:500]}
                        else:
                            logger.warning(f"CRM {platform} returned {resp.status}: {body[:200]}")
                            return {"status": "error", "code": resp.status, "response": body[:500]}
            except asyncio.TimeoutError:
                logger.warning(f"CRM {platform} timeout (attempt {attempt + 1})")
            except Exception as e:
                logger.warning(f"CRM {platform} error (attempt {attempt + 1}): {e}")
            if attempt < 2:
                await asyncio.sleep(2 ** attempt)

        return {"status": "failed", "error": "All retries exhausted"}

    def _get_target(self, platform: str) -> Optional[Dict]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute(
                    "SELECT * FROM webhook_targets WHERE platform=? AND enabled=1 LIMIT 1",
                    (platform.lower(),),
                ).fetchone()
                return dict(row) if row else None
        except Exception:
            return None

    async def add_webhook(self, platform: str, url: str, api_key: Optional[str] = None) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "INSERT INTO webhook_targets (platform, url, api_key) VALUES (?, ?, ?)",
                (platform.lower(), url, api_key),
            )
            conn.commit()
            return cur.lastrowid

    async def notify_webhooks(self, event_type: str, data: Dict[str, Any]):
        for webhook in self.webhooks + self._get_all_targets():
            url = webhook.get("url")
            if not url:
                continue
            payload = {"event": event_type, "data": data, "timestamp": datetime.now().isoformat()}
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        if resp.ok:
                            logger.info(f"Webhook {url} notified for {event_type}")
                        else:
                            logger.warning(f"Webhook {url} error: {resp.status}")
            except Exception as e:
                logger.error(f"Webhook {url} failed: {e}")

    def _get_all_targets(self) -> List[Dict]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                return [dict(r) for r in conn.execute("SELECT * FROM webhook_targets WHERE enabled=1").fetchall()]
        except Exception:
            return []

    def get_sync_log(self, limit: int = 50) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            return [dict(r) for r in conn.execute(
                "SELECT * FROM sync_log ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()]

    def get_stats(self) -> Dict:
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM sync_log").fetchone()[0]
            synced = conn.execute("SELECT COUNT(*) FROM sync_log WHERE status='synced'").fetchone()[0]
            failed = conn.execute("SELECT COUNT(*) FROM sync_log WHERE status='failed'").fetchone()[0]
            logged = conn.execute("SELECT COUNT(*) FROM sync_log WHERE status='logged'").fetchone()[0]
        return {"total": total, "synced": synced, "failed": failed, "logged": logged}


crm_sync = CRMSync()
