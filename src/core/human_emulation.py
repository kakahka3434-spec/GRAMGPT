import asyncio
import random
import logging
from typing import Dict

logger = logging.getLogger(__name__)

class HumanEmulationEngine:
    def __init__(self, dna: Dict = None):
        self.wpm = dna.get("typing_speed_wpm", 150) if dna else 150
        self.error_rate = dna.get("typo_frequency", 0.03) if dna else 0.03

    async def get_typing_delay(self, text: str) -> float:
        word_count = len(text.split())
        base_delay = (word_count / self.wpm) * 60
        jitter = random.uniform(0.8, 1.2)
        return max(1.0, base_delay * jitter)

    async def wait_before_action(self, min_sec: float = 1.0, max_sec: float = 5.0):
        delay = random.uniform(min_sec, max_sec)
        await asyncio.sleep(delay)

    async def simulate_organic_lifecycle(self, account_id: str):
        """Simulates account activity like reading posts and reacting."""
        logger.info(f"Account {account_id} is consuming content...")
        # Simulate browsing
        for _ in range(random.randint(2, 5)):
            await self.wait_before_action(5, 15)
            if random.random() < 0.3:
                logger.info(f"Account {account_id} reacted to a post.")

human_engine = HumanEmulationEngine()
