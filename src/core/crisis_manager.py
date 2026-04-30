import logging
from typing import List, Dict
from src.core.openai_client import openai_client

logger = logging.getLogger(__name__)

class AICrisisManager:
    def __init__(self):
        self.report_threshold = 5

    async def detect_crisis(self, account_id: str, current_reports: int):
        """Monitors reports and triggers auto-pause if threshold met."""
        if current_reports >= self.report_threshold:
            logger.warning(f"CRISIS DETECTED for account {account_id}! Initiating Auto-Pause.")
            return await self.generate_neutralization_strategy(account_id, "High report volume")
        return None

    async def generate_neutralization_strategy(self, account_id: str, reason: str) -> Dict:
        """AI analyzes the crisis and proposes 3 action variants."""
        prompt = (
            f"АККАУНТ: {account_id}\n"
            f"ПРИЧИНА КРИЗИСА: {reason}\n\n"
            "Проанализируй ситуацию и предложи 3 варианта действий для нейтрализации угрозы бана "
            "и восстановления репутации аккаунта. Ответ верни на русском."
        )
        messages = [{"role": "user", "content": prompt}]
        analysis = await openai_client.get_chat_response(0, messages)

        return {
            "account_id": account_id,
            "status": "paused",
            "analysis": analysis,
            "options": [
                "1. Смена IP + Пауза 48 часов",
                "2. Удаление последних сообщений + Масс-реакции на 'белые' каналы",
                "3. Мимикрия под личный аккаунт (Stories, переписки с друзьями)"
            ]
        }

crisis_manager = AICrisisManager()
