import json
import logging
import os
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from src.db.database import db

logger = logging.getLogger(__name__)


class ReferralSystem:
    """
    Referral tracking with bonuses, leaderboard, and stats.
    Referrer gets bonus when referred user performs actions.
    """

    def __init__(self, db_path: str = "data/referrals.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self._init_db()
        self.bonus_per_referral = 20
        self.commission_rate = 30

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS referrals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    referrer_id INTEGER NOT NULL,
                    referred_id INTEGER NOT NULL UNIQUE,
                    status TEXT DEFAULT 'active',
                    bonus_given INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT (datetime('now')),
                    converted_at TEXT
                );
                CREATE TABLE IF NOT EXISTS referral_earnings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    amount REAL DEFAULT 0,
                    source TEXT,
                    created_at TEXT DEFAULT (datetime('now'))
                );
                CREATE TABLE IF NOT EXISTS referral_codes (
                    code TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    created_at TEXT DEFAULT (datetime('now'))
                );
            """)

    def generate_referral_link(self, user_id: int) -> str:
        code = self._get_or_create_code(user_id)
        return f"https://t.me/gramgpt_bot?start={code}"

    def _get_or_create_code(self, user_id: int) -> str:
        try:
            with sqlite3.connect(self.db_path) as conn:
                row = conn.execute("SELECT code FROM referral_codes WHERE user_id=?", (user_id,)).fetchone()
                if row:
                    return row[0]
                code = f"ref_{user_id}"
                conn.execute("INSERT OR IGNORE INTO referral_codes (code, user_id) VALUES (?, ?)", (code, user_id))
                conn.commit()
                return code
        except Exception:
            return f"ref_{user_id}"

    async def process_new_user(self, user_id: int, start_command: str) -> Optional[int]:
        if not start_command or not start_command.startswith("ref_"):
            return None

        try:
            referrer_id = int(start_command.split("_")[1])
        except (ValueError, IndexError):
            return None

        if user_id == referrer_id:
            return None

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR IGNORE INTO referrals (referrer_id, referred_id) VALUES (?, ?)",
                    (referrer_id, user_id),
                )
                conn.execute(
                    "INSERT INTO referral_earnings (user_id, amount, source) VALUES (?, ?, 'referral_bonus')",
                    (referrer_id, self.bonus_per_referral),
                )
                conn.commit()
            logger.info(f"User {user_id} referred by {referrer_id}")
            db.add_referral(user_id, referrer_id)
            return referrer_id
        except Exception as e:
            logger.error(f"Referral processing failed: {e}")
            return None

    async def record_conversion(self, user_id: int, amount: float):
        """Called when referred user makes a purchase or reaches milestone."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT id FROM referrals WHERE referred_id=? AND bonus_given=0",
                (user_id,),
            ).fetchone()
            if row:
                commission = amount * self.commission_rate / 100
                conn.execute(
                    "UPDATE referrals SET bonus_given=1, converted_at=datetime('now') WHERE id=?",
                    (row[0],),
                )
                conn.execute(
                    "INSERT INTO referral_earnings (user_id, amount, source) VALUES (?, ?, 'conversion')",
                    (conn.execute("SELECT referrer_id FROM referrals WHERE id=?", (row[0],)).fetchone()[0], commission),
                )
                conn.commit()
                return commission
        return 0.0

    def get_stats(self, user_id: int) -> Dict:
        try:
            with sqlite3.connect(self.db_path) as conn:
                total_refs = conn.execute(
                    "SELECT COUNT(*) FROM referrals WHERE referrer_id=?", (user_id,)
                ).fetchone()[0]
                active_refs = conn.execute(
                    "SELECT COUNT(*) FROM referrals WHERE referrer_id=? AND status='active'", (user_id,)
                ).fetchone()[0]
                earnings = conn.execute(
                    "SELECT COALESCE(SUM(amount), 0) FROM referral_earnings WHERE user_id=?", (user_id,)
                ).fetchone()[0]
                recent = conn.execute(
                    "SELECT referred_id, created_at FROM referrals WHERE referrer_id=? ORDER BY created_at DESC LIMIT 5",
                    (user_id,),
                ).fetchall()
        except Exception:
            total_refs = active_refs = earnings = 0
            recent = []

        return {
            "total_referrals": total_refs,
            "active_referrals": active_refs,
            "earnings": earnings,
            "commission_rate": self.commission_rate,
            "recent": [{"referred_id": r[0], "date": r[1]} for r in recent],
            "link": self.generate_referral_link(user_id),
        }

    def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute("""
                    SELECT e.user_id, SUM(e.amount) as total, COUNT(r.id) as referrals
                    FROM referral_earnings e
                    LEFT JOIN referrals r ON r.referrer_id = e.user_id
                    GROUP BY e.user_id
                    ORDER BY total DESC LIMIT ?
                """, (limit,)).fetchall()
                return [dict(r) for r in rows]
        except Exception:
            return []


referral_system = ReferralSystem()
