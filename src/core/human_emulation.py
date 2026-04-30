import asyncio
import random
import logging

logger = logging.getLogger(__name__)

class HumanEmulationEngine:
    def __init__(self, wpm: int = 150):
        self.wpm = wpm  # Words per minute
        self.error_rate = 0.03  # 3% chance of typo

    async def get_typing_delay(self, text: str) -> float:
        """Calculate realistic typing delay based on text length."""
        word_count = len(text.split())
        base_delay = (word_count / self.wpm) * 60
        # Add jitter
        jitter = random.uniform(0.8, 1.2)
        return max(1.0, base_delay * jitter)

    def simulate_typo(self, text: str) -> str:
        """Occasionally introduce and correct a typo."""
        if len(text) < 10 or random.random() > self.error_rate:
            return text

        # Simple typo simulation
        pos = random.randint(5, len(text) - 1)
        typo_text = text[:pos] + random.choice("qwertyuiop") + text[pos+1:]
        correction = f"\n\n*Исправление: {text[pos:pos+5]}*" # Simplified Russian correction
        return typo_text # In a real bot, we'd send typo then edit message

    async def wait_before_action(self, min_sec: float = 1.0, max_sec: float = 5.0):
        """Random pause before performing an action."""
        delay = random.uniform(min_sec, max_sec)
        await asyncio.sleep(delay)

human_engine = HumanEmulationEngine()
