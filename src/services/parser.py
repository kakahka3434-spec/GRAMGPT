from typing import Dict, Any
from src.core.openai_client import openai_client

class SmartParser:
    async def analyze_user_behavior(self, user_data: str) -> Dict[str, Any]:
        """
        Analyzes user behavior using AI.
        user_data should contain recent messages or channel activity.
        """
        prompt = (
            "Проведи поведенческий анализ пользователя на основе его сообщений:\n"
            f"{user_data}\n\n"
            "Верни JSON с полями:\n"
            "- tone: (позитивный/негативный/нейтральный)\n"
            "- interests: (список интересов)\n"
            "- activity_level: (высокий/средний/низкий)\n"
            "- buy_readiness: (0-100)\n"
            "- recommendation: (как лучше к нему обратиться)"
        )

        # We wrap it in a mock-friendly way
        messages = [{"role": "user", "content": prompt}]
        # Passing a dummy chat_id for settings lookup
        response = await openai_client.get_chat_response(0, messages)

        return {
            "raw_analysis": response,
            "ready_to_buy": "высокая" in response.lower() or "80" in response
        }

smart_parser = SmartParser()
