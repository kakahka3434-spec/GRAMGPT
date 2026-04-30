import sqlite3
import json
from typing import List, Dict

class Database:
    def __init__(self, db_path: str = "gramgpt.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
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
            # Return in chronological order (oldest first)
            return [{"role": r, "content": c} for r, c in reversed(rows)]

    def clear_history(self, chat_id: int):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
            conn.commit()

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
