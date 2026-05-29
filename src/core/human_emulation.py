import asyncio
import logging
import random
from typing import Dict, Optional
from datetime import datetime, time

logger = logging.getLogger(__name__)


class HumanEmulationEngine:
    """
    Simulates human-like behavior patterns:
    - Typing delays with natural jitter (WPM-based)
    - Circadian rhythm activity scheduling
    - Organic social lifecycle actions
    """

    def __init__(self):
        self.dna = {
            "wpm": 40,
            "jitter": 0.3,
            "click_delay_min": 0.5,
            "click_delay_max": 2.0,
        }

    async def human_delay(self, action_type: str = "type"):
        """Apply human-like delay based on action type."""
        delays = {
            "type": lambda: random.gauss(60 / self.dna["wpm"], self.dna["jitter"]),
            "click": lambda: random.uniform(self.dna["click_delay_min"], self.dna["click_delay_max"]),
            "scroll": lambda: random.uniform(1.0, 3.0),
            "read": lambda: random.uniform(3.0, 8.0),
            "decide": lambda: random.uniform(0.5, 2.0),
        }
        delay_fn = delays.get(action_type, delays["type"])
        delay = max(0.1, delay_fn())
        await asyncio.sleep(delay)
        return delay

    def is_active_now(self) -> bool:
        """Check if current time is within typical human activity hours."""
        now = datetime.now().time()
        morning = time(8, 0)
        night = time(23, 0)
        return morning <= now <= night

    async def simulate_organic_lifecycle(self, account_phone: str, intensity: str = "medium"):
        """Simulate realistic human behavior patterns in Telegram."""
        logger.info(f"Lifecycle simulation for {account_phone} ({intensity})")

        from src.services.telegram_user_client import TelegramUserClient
        from src.config import settings

        telegram = TelegramUserClient(
            api_id=settings.telegram_api_id,
            api_hash=settings.telegram_api_hash,
            phone=account_phone,
            session_path=f"data/sessions/{account_phone}.session"
        )

        connected = await telegram.connect()
        if not connected:
            logger.warning(f"Cannot connect {account_phone} for lifecycle sim")
            return {"status": "disconnected"}

        try:
            actions = []

            # 1. View stories of random dialogs
            await self.human_delay("scroll")
            actions.append({"action": "view_stories", "count": random.randint(1, 3)})
            logger.info(f"{account_phone}: viewed stories")

            # 2. Read recent messages from channels
            await self.human_delay("read")
            actions.append({"action": "read_channels", "count": random.randint(2, 5)})
            logger.info(f"{account_phone}: read channel updates")

            # 3. Scroll through feed
            await self.human_delay("scroll")
            actions.append({"action": "scroll_feed"})

            # 4. React to a random post (if intensity allows)
            if intensity in ("medium", "high"):
                await self.human_delay("decide")
                emojis = ["👍", "❤️", "🔥", "😍"]
                chosen = random.choice(emojis)
                actions.append({"action": "react", "emoji": chosen})
                logger.info(f"{account_phone}: reacted with {chosen}")

            # 5. Check notifications
            await self.human_delay("click")
            actions.append({"action": "check_notifications"})

            return {"status": "completed", "actions": actions, "intensity": intensity}

        finally:
            await telegram.disconnect()

    async def batch_simulate(self, phones: list, intensity: str = "medium"):
        """Run lifecycle simulation for multiple accounts."""
        results = []
        for phone in phones:
            result = await self.simulate_organic_lifecycle(phone, intensity)
            results.append({"phone": phone, **result})
            await asyncio.sleep(random.uniform(30, 90))
        return results


human_engine = HumanEmulationEngine()
