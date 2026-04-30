from enum import Enum
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class Channel(Enum):
    TELEGRAM = "tg"
    WHATSAPP = "wa"
    INSTAGRAM = "ig"
    EMAIL = "email"
    SMS = "sms"

class MultiChannelRouter:
    def __init__(self):
        self.unified_inbox: List[Dict] = []

    async def route_lead(self, lead_id: int, target_channel: Channel, message: str) -> Dict[str, Any]:
        """Routes message and logs to Unified Inbox."""
        logger.info(f"Routing to {target_channel.name} | Lead {lead_id}: {message[:20]}")

        event = {
            "lead_id": lead_id,
            "channel": target_channel.value,
            "message": message,
            "direction": "outbound"
        }
        self.unified_inbox.append(event)

        # Simulated Channel Integrations
        if target_channel == Channel.WHATSAPP:
            return {"status": "sent", "channel_api": "Cloud API"}
        elif target_channel == Channel.INSTAGRAM:
            return {"status": "sent", "channel_api": "Graph API"}

        return {"status": "queued"}

    def get_unified_history(self, lead_id: int) -> List[Dict]:
        """Unified Inbox: Get all interactions across all channels."""
        return [e for e in self.unified_inbox if e["lead_id"] == lead_id]

channel_router = MultiChannelRouter()
