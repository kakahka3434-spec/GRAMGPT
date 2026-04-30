import sqlite3
import json
from typing import List, Dict, Any, Optional

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
                    behavioral_profile TEXT,
                    channel_origin TEXT,
                    status TEXT DEFAULT 'new',
                    last_contact DATETIME
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT,
                    payload TEXT,
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

    def add_account(self, phone: str, device: str, fp: str, proxy: str, dna: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO accounts (phone, device_type, fingerprint, proxy, dna_profile) VALUES (?, ?, ?, ?, ?)",
                (phone, device, fp, proxy, dna)
            )
            conn.commit()

    def update_risk_score(self, phone: str, score: int):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE accounts SET risk_score = ? WHERE phone = ?", (score, phone))
            conn.commit()

    def create_campaign(self, name: str, goal: str, strategy: Dict[str, Any]):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO campaigns (name, goal, strategy_json) VALUES (?, ?, ?)",
                (name, goal, json.dumps(strategy))
            )
            conn.commit()

    def upsert_lead(self, tg_id: int, username: str, score: int, profile: Dict[str, Any]):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO leads (tg_id, username, engagement_score, behavioral_profile, last_contact)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(tg_id) DO UPDATE SET
                    engagement_score = excluded.engagement_score,
                    behavioral_profile = excluded.behavioral_profile,
                    last_contact = CURRENT_TIMESTAMP
            """, (tg_id, username, score, json.dumps(profile)))
            conn.commit()

    def add_message(self, chat_id: int, role: str, content: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT INTO messages (chat_id, role, content) VALUES (?, ?, ?)", (chat_id, role, content))
            conn.commit()

    def get_history(self, chat_id: int, limit: int = 20) -> List[Dict[str, str]]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT role, content FROM messages WHERE chat_id = ? ORDER BY id DESC LIMIT ?", (chat_id, limit))
            rows = cursor.fetchall()
            return [{"role": r, "content": c} for r, c in reversed(rows)]

    def clear_history(self, chat_id: int):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
            conn.commit()

    def set_user_model(self, chat_id: int, model_name: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT OR REPLACE INTO user_settings (chat_id, model_name) VALUES (?, ?)", (chat_id, model_name))
            conn.commit()

    def get_user_model(self, chat_id: int) -> str:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT model_name FROM user_settings WHERE chat_id = ?", (chat_id,))
            row = cursor.fetchone()
            return row[0] if row else "gpt-4o"

db = Database()
