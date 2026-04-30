import logging
import aiohttp
from typing import Dict, Any

logger = logging.getLogger(__name__)

class CRMSync:
    def __init__(self):
        self.webhooks = []

    async def sync_lead(self, lead_data: Dict[str, Any], platform: str = "amoCRM"):
        """Sends lead data to a CRM via API or Webhook."""
        logger.info(f"Syncing lead to {platform}: {lead_data.get('username')}")

        # Simulated API call
        async with aiohttp.ClientSession() as session:
            # payload = {"name": lead_data['username'], "status": "new_lead"}
            # await session.post(f"https://{platform}.api.com/v1/leads", json=payload)
            pass

        return {"status": "synced", "platform": platform}

    async def notify_webhooks(self, event_type: str, data: Dict[str, Any]):
        """Notifies external services about events (e.g., new message, new lead)."""
        for webhook_url in self.webhooks:
            logger.info(f"Notifying webhook {webhook_url} for event {event_type}")
            # await session.post(webhook_url, json={"event": event_type, "data": data})

crm_sync = CRMSync()
