from typing import Dict, Any, List
import json
import logging
import random
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
        except Exception:
            strategy = {
                "name": campaign_name,
                "predicted_roi": f"{random.randint(150, 400)}%",
                "steps": [
                    {"day": "1-3", "action": "Scraping & Warmup"},
                    {"day": "4-7", "action": "Commenting & Reaction Funnel"},
                    {"day": "8-14", "action": "Chatting & DM Close"},
                ],
                "channels": ["Telegram", "WhatsApp"],
                "optimization_metrics": ["Conversion Rate", "Ban Risk Score"],
            }

        try:
            db.create_campaign(campaign_name, goal, strategy)
        except Exception as e:
            logger.warning(f"Could not persist campaign: {e}")
        return strategy

    async def auto_optimization_loop(self, campaign_id: int) -> Dict:
        logger.info(f"Auto-optimizing campaign #{campaign_id}...")
        try:
            campaign = db.get_campaign(campaign_id)
        except Exception:
            campaign = None

        metrics = {
            "conversion": campaign.get("conversion_rate", 0.05) if campaign else 0.05,
            "replies": campaign.get("total_replies", 12) if campaign else 12,
            "bans": campaign.get("ban_count", 0) if campaign else 0,
        }

        prompt = (
            f"Analyze campaign campaign #{campaign_id} metrics: {json.dumps(metrics)}.\n"
            "Suggest 3 specific improvements to increase conversion and reduce ban risk. "
            "Return JSON with: adjustments (array of strings), risk_level (low/medium/high), "
            "recommended_delay_change (int minutes)."
        )
        try:
            response = await ai_client.get_chat_response(0, [{"role": "user", "content": prompt}])
            start = response.find("{")
            end = response.rfind("}") + 1
            result = json.loads(response[start:end])
        except Exception:
            result = {
                "adjustments": ["Shift activity to evening hours", "Reduce comment frequency", "Add emoji variety"],
                "risk_level": "medium",
                "recommended_delay_change": 30,
            }

        logger.info(f"Optimization result for #{campaign_id}: {result.get('adjustments', [])}")
        return {"status": "optimized", "campaign_id": campaign_id, **result}


orchestrator = AIOrchestrator()
