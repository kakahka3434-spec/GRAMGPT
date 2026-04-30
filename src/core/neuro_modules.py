from src.core.openai_client import openai_client
from typing import List, Dict

class NeuroCommenting:
    async def generate_comment(self, post_text: str, recent_comments: List[str]) -> str:
        prompt = (
            f"Прочитай пост: {post_text[:300]}\n"
            f"Последние комментарии: {recent_comments}\n"
            "Напиши осмысленный комментарий, который впишется в беседу, "
            "будет созвучен тону автора и спровоцирует ответ (байты на вопрос)."
        )
        messages = [{"role": "user", "content": prompt}]
        return await openai_client.get_chat_response(0, messages)

class NeuroChatting:
    async def handle_objection(self, user_message: str, history: List[Dict]) -> str:
        prompt = (
            f"Пользователь возражает: '{user_message}'\n"
            "Твоя задача — отработать возражение профессионально, "
            "используя психологические триггеры и органично вплетая кейсы/отзывы."
        )
        # Combine history with prompt
        full_history = history + [{"role": "user", "content": prompt}]
        return await openai_client.get_chat_response(0, full_history)

neuro_commenting = NeuroCommenting()
neuro_chatting = NeuroChatting()
