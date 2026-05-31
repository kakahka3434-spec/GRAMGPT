from typing import Dict, Any, List
import json
import logging
from src.core.ai_client import ai_client
from src.db.database import db

logger = logging.getLogger(__name__)


class AIOrchestrator:
    def __init__(self):
        self.optimization_interval = 7200

    async def create_campaign_strategy(self, campaign_name: str, goal: str) -> Dict[str, Any]:
        prompt = (
            f"Create a detailed marketing strategy 2.0 for campaign '{campaign_name}'.\n"
            f"Goal: {goal}\n\n"
            "Include:\n"
            "1. Stages (Parsing, Warmup, Engagement, Closing).\n"
            "2. Predicted ROI estimate based on similar campaigns.\n"
            "3. Recommended channels (TG, WA, Email).\n"
            "4. Optimization plan.\n"
            "Return JSON object with keys: name, predicted_roi, steps (array of {day, action}), channels, optimization_metrics."
        )
        messages = [{"role": "user", "content": prompt}]
        try:
            response = await ai_client.get_chat_response(0, messages)
            start = response.find("{")
            end = response.rfind("}") + 1
            strategy = json.loads(response[start:end])
        except Exception as e:
            logger.warning(f"AI strategy generation failed, using DB-driven defaults: {e}")
            strategy = self._default_strategy(campaign_name, goal)

        try:
            db.create_campaign(campaign_name, goal, strategy)
        except Exception as e:
            logger.warning(f"Could not persist campaign: {e}")
        return strategy

    def _default_strategy(self, campaign_name: str, goal: str) -> Dict[str, Any]:
        roi_estimates = {
            "leads": "250-400%", "traffic": "150-300%",
            "engagement": "100-200%", "sales": "300-600%",
        }
        steps_by_goal = {
            "leads": [
                {"day": "1-3", "action": "Парсинг целевых каналов"},
                {"day": "4-7", "action": "Прогрев + нейрокомментинг"},
                {"day": "8-12", "action": "Chatting + закрытие в ЛС"},
                {"day": "13-14", "action": "Анализ и оптимизация"},
            ],
            "traffic": [
                {"day": "1-2", "action": "Парсинг каналов по теме"},
                {"day": "3-7", "action": "Массовый комментинг"},
                {"day": "8-14", "action": "Retargeting и реакции"},
            ],
            "sales": [
                {"day": "1-3", "action": "Сбор тёплой аудитории"},
                {"day": "4-8", "action": "НейроДиалоги + автоворонка"},
                {"day": "9-14", "action": "Закрытие сделок через CRM"},
            ],
        }
        return {
            "name": campaign_name,
            "predicted_roi": roi_estimates.get(goal, "150-300%"),
            "steps": steps_by_goal.get(goal, steps_by_goal["leads"]),
            "channels": ["Telegram"],
            "optimization_metrics": ["Conversion Rate", "Ban Risk Score", "CPL"],
        }

    async def auto_optimization_loop(self, campaign_id: int) -> Dict:
        logger.info(f"Auto-optimizing campaign #{campaign_id}...")
        try:
            campaign = db.get_campaign(campaign_id)
        except Exception:
            campaign = None

        if campaign:
            metrics = {
                "conversion": campaign.get("conversion_rate", 0.05),
                "replies": campaign.get("total_replies", 0),
                "bans": campaign.get("ban_count", 0),
            }
        else:
            conn = db._get_connection()
            row = conn.execute("SELECT id, status FROM campaigns WHERE id = ?", [campaign_id]).fetchone()
            metrics = {"conversion": 0.0, "replies": 0, "bans": 0, "campaign_found": row is not None}
            conn.close()

        prompt = (
            f"Analyze campaign #{campaign_id} metrics: {json.dumps(metrics)}.\n"
            "Suggest 3 specific improvements to increase conversion and reduce ban risk. "
            "Return JSON with: adjustments (array of strings), risk_level (low/medium/high), "
            "recommended_delay_change (int minutes)."
        )
        try:
            response = await ai_client.get_chat_response(0, [{"role": "user", "content": prompt}])
            start = response.find("{")
            end = response.rfind("}") + 1
            result = json.loads(response[start:end])
        except Exception as e:
            logger.warning(f"AI optimization failed, using metric-driven defaults: {e}")
            result = self._default_optimization(metrics.get("bans", 0), metrics.get("conversion", 0))

        logger.info(f"Optimization result for #{campaign_id}: {result.get('adjustments', [])}")
        return {"status": "optimized", "campaign_id": campaign_id, **result}

    def _default_optimization(self, ban_count: int, conversion: float) -> Dict:
        adjustments = []
        if ban_count > 2:
            adjustments.append("Increase comment delay by 60s — high ban rate detected")
            adjustments.append("Reduce daily comment volume by 30%")
        elif conversion < 0.02:
            adjustments.append("Refine target channels — low conversion rate")
            adjustments.append("Test different comment styles (expert vs supportive)")
        else:
            adjustments.append("Current performance is stable — monitor conversion funnel")
            adjustments.append("Consider A/B testing prompt templates")

        risk_level = "high" if ban_count > 5 else "medium" if ban_count > 2 else "low"
        return {
            "adjustments": adjustments,
            "risk_level": risk_level,
            "recommended_delay_change": 60 if ban_count > 2 else 15,
        }


orchestrator = AIOrchestrator()
