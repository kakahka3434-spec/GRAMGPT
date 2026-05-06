from src.db.database import db
from src.db.comment_memory import comment_memory
from typing import List, Dict

class ConversationMemory:
    def add_message(self, chat_id: int, role: str, content: str):
        db.add_message(chat_id, role, content)

    def get_history(self, chat_id: int) -> List[Dict[str, str]]:
        return db.get_history(chat_id)

    def clear_history(self, chat_id: int):
        db.clear_history(chat_id)

memory = ConversationMemory()
