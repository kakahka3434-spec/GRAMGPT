from collections import defaultdict
from typing import List, Dict

class ConversationMemory:
    def __init__(self, limit: int = 20):
        self.limit = limit
        self.storage: Dict[int, List[Dict[str, str]]] = defaultdict(list)

    def add_message(self, chat_id: int, role: str, content: str):
        self.storage[chat_id].append({"role": role, "content": content})
        if len(self.storage[chat_id]) > self.limit:
            self.storage[chat_id] = self.storage[chat_id][-self.limit:]

    def get_history(self, chat_id: int) -> List[Dict[str, str]]:
        return self.storage[chat_id]

    def clear_history(self, chat_id: int):
        self.storage[chat_id] = []

memory = ConversationMemory()
