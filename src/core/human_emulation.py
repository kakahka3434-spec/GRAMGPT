import asyncio
import random
import logging
from datetime import datetime
from typing import Dict

logger = logging.getLogger(__name__)

class HumanEmulationEngine:
    def __init__(self, dna: Dict = None):
        self.wpm = dna.get("typing_speed_wpm", 150) if dna else 150
        self.error_rate = dna.get("typo_frequency", 0.03) if dna else 0.03
        self.timezone_offset = dna.get("timezone", 0) if dna else 0
        self.rhythm = dna.get("preferred_hours", "work_hours") if dna else "work_hours"

    async def get_typing_delay(self, text: str) -> float:
        word_count = len(text.split())
        base_delay = (word_count / self.wpm) * 60
        jitter = random.uniform(0.8, 1.2)
        return max(1.0, base_delay * jitter)

    async def wait_before_action(self, min_sec: float = 1.0, max_sec: float = 5.0):
        delay = random.uniform(min_sec, max_sec)
        await asyncio.sleep(delay)

    def is_active_now(self) -> bool:
        """Biological Rhythm Sync: Check if the account should be active based on its DNA."""
        hour = (datetime.now().hour + self.timezone_offset) % 24

        if self.rhythm == "morning":
            return 6 <= hour <= 12
        elif self.rhythm == "evening":
            return 18 <= hour <= 23
        elif self.rhythm == "night":
            return 0 <= hour <= 5
        else: # work_hours
            return 9 <= hour <= 18

    async def simulate_organic_lifecycle(self, account_id: str):
        """Social Graph & Content Digestion logic."""
        if not self.is_active_now():
            logger.info(f"Account {account_id} is resting (circadian rhythm sync).")
            return

        logger.info(f"Account {account_id} is digesting content and building social graph...")
        # Simulate social actions
        actions = ["read_post", "react", "view_story", "message_friend"]
        for _ in range(random.randint(2, 6)):
            action = random.choice(actions)
            logger.info(f"Action: {account_id} performing {action}")
            await self.wait_before_action(10, 30)

human_engine = HumanEmulationEngine()
