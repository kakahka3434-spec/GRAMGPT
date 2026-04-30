import pytest
from src.core.human_emulation import HumanEmulationEngine

def test_typing_delay():
    engine = HumanEmulationEngine(wpm=100)
    text = "Hello world this is a test" # 6 words
    # (6/100)*60 = 3.6s
    delay = asyncio.run(engine.get_typing_delay(text))
    assert delay >= 1.0

import asyncio
