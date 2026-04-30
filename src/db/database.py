import sqlite3
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str = "gramgpt.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    phone TEXT UNIQUE,
                    device_type TEXT,
                    fingerprint TEXT,
                    proxy TEXT,
                    status TEXT DEFAULT 'idle',
                    risk_score INTEGER DEFAULT 0,
                    dna_profile TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS campaigns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    goal TEXT,
                    strategy_json TEXT,
                    roi_predicted TEXT,
                    status TEXT DEFAULT 'planned',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tg_id INTEGER UNIQUE,
                    username TEXT,
                    engagement_score INTEGER DEFAULT 0,
                    ltv_estimate REAL DEFAULT 0,
                    behavioral_profile TEXT,
                    status TEXT DEFAULT 'new',
                    last_contact DATETIME
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    campaign_id INTEGER,
                    event_type TEXT,
                    cost REAL DEFAULT 0,
                    revenue REAL DEFAULT 0,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER,
                    role TEXT,
                    content TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_settings (
                    chat_id INTEGER PRIMARY KEY,
                    model_name TEXT DEFAULT 'gpt-4o'
                )
            """)
            conn.commit()

    def create_campaign(self, name: str, goal: str, strategy: Dict[str, Any]):
        roi = strategy.get("predicted_roi", "N/A")
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO campaigns (name, goal, strategy_json, roi_predicted) VALUES (?, ?, ?, ?)",
                (name, goal, json.dumps(strategy), str(roi))
            )
            conn.commit()

    def get_roi_report(self, campaign_id: int) -> Dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT SUM(cost), SUM(revenue) FROM analytics WHERE campaign_id = ?",
                (campaign_id,)
            )
            cost, revenue = cursor.fetchone()
            cost = cost or 1
            revenue = revenue or 0
            return {
                "roi_actual": f"{(revenue/cost)*100:.1f}%",
                "total_revenue": revenue,
                "total_cost": cost
            }

    # Bot Message & History Methods
    def add_message(self, chat_id: int, role: str, content: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO messages (chat_id, role, content) VALUES (?, ?, ?)",
                (chat_id, role, content)
            )
            conn.commit()

    def get_history(self, chat_id: int, limit: int = 20) -> List[Dict[str, str]]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT role, content FROM messages WHERE chat_id = ? ORDER BY id DESC LIMIT ?",
                (chat_id, limit)
            )
            rows = cursor.fetchall()
            return [{"role": r, "content": c} for r, c in reversed(rows)]

    def clear_history(self, chat_id: int):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
            conn.commit()

    # User Settings Methods
    def set_user_model(self, chat_id: int, model_name: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO user_settings (chat_id, model_name) VALUES (?, ?)",
                (chat_id, model_name)
            )
            conn.commit()

    def get_user_model(self, chat_id: int) -> str:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT model_name FROM user_settings WHERE chat_id = ?", (chat_id,))
            row = cursor.fetchone()
            return row[0] if row else "gpt-4o"

db = Database()
