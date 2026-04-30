from enum import Enum
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class Channel(Enum):
    TELEGRAM = "tg"
    WHATSAPP = "wa"
    INSTAGRAM = "ig"
    EMAIL = "email"

class MultiChannelRouter:
    async def route_lead(self, lead_id: int, target_channel: Channel, message: str):
        """Routes a message to a specific channel for a lead."""
        logger.info(f"Routing message to {target_channel.value} for lead {lead_id}: {message[:30]}...")

        if target_channel == Channel.TELEGRAM:
            # Call TG bot service
            pass
        elif target_channel == Channel.WHATSAPP:
            # Call WA API
            pass
        elif target_channel == Channel.INSTAGRAM:
            # Call IG API
            pass

        return {"status": "sent", "channel": target_channel.value}

channel_router = MultiChannelRouter()
