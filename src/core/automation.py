import aiohttp
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class AutomationEngine:
    async def trigger_webhook(self, url: str, payload: Dict[str, Any]):
        """Sends an event to Zapier, Make, or any custom Webhook."""
        logger.info(f"Triggering outbound automation to {url}")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    return await response.json()
        except Exception as e:
            logger.error(f"Webhook trigger failed: {e}")
            return {"status": "error", "message": str(e)}

automation = AutomationEngine()
