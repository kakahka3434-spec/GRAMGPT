import asyncio
import pytest
from src.core.human_emulation import HumanEmulationEngine


@pytest.mark.asyncio
async def test_human_delay():
    engine = HumanEmulationEngine()
    delay = await engine.human_delay("click")
    assert delay >= 0.1


def test_is_active_now():
    engine = HumanEmulationEngine()
    result = engine.is_active_now()
    assert isinstance(result, bool)


@pytest.mark.asyncio
async def test_human_delay_type():
    engine = HumanEmulationEngine()
    delay = await engine.human_delay("type")
    assert delay >= 0.1


@pytest.mark.asyncio
async def test_human_delay_read():
    engine = HumanEmulationEngine()
    delay = await engine.human_delay("read")
    assert delay >= 1.0
