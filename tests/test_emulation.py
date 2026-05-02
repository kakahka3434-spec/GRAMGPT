import asyncio
import pytest
from src.core.human_emulation import HumanEmulationEngine


def test_typing_delay():
    dna = {"typing_speed_wpm": 100}
    engine = HumanEmulationEngine(dna=dna)
    text = "Hello world this is a test"  # 6 words
    # (6/100)*60 = 3.6s base
    delay = asyncio.run(engine.get_typing_delay(text))
    assert delay >= 1.0


def test_is_active_now():
    engine = HumanEmulationEngine()
    result = engine.is_active_now()
    assert isinstance(result, bool)


def test_wait_before_action():
    engine = HumanEmulationEngine()
    asyncio.run(engine.wait_before_action(0.01, 0.02))
