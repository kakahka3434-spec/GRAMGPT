from src.core.openai_client import openai_client
from typing import List, Dict, Optional
import random

class NeuroCommenting:
    async def generate_comment(self, post_text: str, recent_comments: List[str]) -> str:
        prompt = (
            f"КОНТЕКСТ ПОСТА: {post_text[:500]}\n"
            f"КОММЕНТАРИИ: {recent_comments}\n\n"
            "Твоя цель: Встроиться в диалог (Thread Hijacking). "
            "Сгенерируй комментарий, который:\n"
            "1. Резонирует с эмоцией поста.\n"
            "2. Задает вопрос, на который хочется ответить (Question Baiting).\n"
            "3. Использует уместные эмодзи."
        )
        messages = [{"role": "user", "content": prompt}]
        return await openai_client.get_chat_response(0, messages)

class NeuroChatting:
    def __init__(self):
        self.objection_library_size = 500

    async def handle_objection(self, user_message: str, history: List[Dict]) -> str:
        prompt = (
            f"Пользователь возражает: '{user_message}'\n"
            "Используй библиотеку из 500+ сценариев для профессиональной отработки. "
            "Добавь Urgency (срочность) и Social Proof (кейсы) органично."
        )
        full_history = history + [{"role": "user", "content": prompt}]
        return await openai_client.get_chat_response(0, full_history)

class MassReactionPro:
    def __init__(self):
        self.reactions = ["👍", "❤️", "🔥", "🤩", "🤔", "👏"]

    def get_reaction_funnel_step(self, stage: int) -> str:
        """Reaction Funnel: 👀 -> 👍 -> ❤️ -> 🔥"""
        funnel = ["👀", "👍", "❤️", "🔥"]
        return funnel[min(stage, len(funnel)-1)]

    async def map_emotion(self, text: str) -> str:
        """Emotional Mapping logic."""
        # Simple heuristic or AI call
        if "круто" in text.lower() or "ого" in text.lower():
            return "🔥"
        return "👍"

neuro_commenting = NeuroCommenting()
neuro_chatting = NeuroChatting()
mass_reaction = MassReactionPro()

class NeuroSabotage:
    async def generate_counter_argument(self, competitor_post: str) -> str:
        """Generates soft informational pressure comments."""
        prompt = (
            f"ПОСТ КОНКУРЕНТА: {competitor_post[:400]}\n\n"
            "Сгенерируй комментарий, который мягко ставит под сомнение эффективность метода конкурента "
            "и намекает, что в GPTGRAM это делается автоматически и лучше. Без прямой рекламы, "
            "в стиле экспертного сомнения."
        )
        messages = [{"role": "user", "content": prompt}]
        return await openai_client.get_chat_response(0, messages)

    async def generate_comparison_article(self, competitor_name: str) -> str:
        """Generates content for 'independent' comparison channels."""
        prompt = (
            f"Сравни GPTGRAM Ultimate и {competitor_name}.\n"
            "Сделай упор на преимуществах GPTGRAM в Anti-Detect 3.0, "
            "Predictive ROI и AI Orchestrator. Тон должен быть аналитическим и объективным."
        )
        messages = [{"role": "user", "content": prompt}]
        return await openai_client.get_chat_response(0, messages)

neuro_sabotage = NeuroSabotage()
