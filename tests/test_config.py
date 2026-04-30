import os
import pytest
from src.config import Settings

def test_settings_load_from_env(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "test_bot_token")
    monkeypatch.setenv("OPENAI_API_KEY", "test_openai_key")
    monkeypatch.setenv("TEMPERATURE", "0.5")

    settings = Settings()
    assert settings.bot_token == "test_bot_token"
    assert settings.openai_api_key == "test_openai_key"
    assert settings.temperature == 0.5
    assert settings.model_name == "gpt-4-turbo"  # Default value
