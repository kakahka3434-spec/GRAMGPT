from typing import Dict, Any
import json
import logging
from src.core.openai_client import openai_client
from src.db.database import db

logger = logging.getLogger(__name__)

class AIOrchestrator:
    async def create_campaign_strategy(self, campaign_name: str, goal: str) -> Dict[str, Any]:
        """Generates a multi-step campaign strategy using AI."""
        prompt = (
            f"Создай детальную маркетинговую стратегию для кампании '{campaign_name}'.\n"
            f"Цель: {goal}\n\n"
            "Стратегия должна включать:\n"
            "1. Этап парсинга (какие каналы/триггеры)\n"
            "2. Этап прогрева (сколько дней, какие реакции)\n"
            "3. Этап взаимодействия (комментинг или DM)\n"
            "4. Ожидаемая конверсия\n\n"
            "Верни только JSON объект."
        )

        messages = [{"role": "user", "content": prompt}]
        response = await openai_client.get_chat_response(0, messages)

        try:
            # Simple attempt to parse JSON from response
            start = response.find("{")
            end = response.rfind("}") + 1
            strategy = json.loads(response[start:end])
        except Exception:
            strategy = {"raw_strategy": response, "steps": ["Parsing", "Warmup", "Engage"]}

        db.create_campaign(campaign_name, goal, strategy)
        return strategy

orchestrator = AIOrchestrator()
