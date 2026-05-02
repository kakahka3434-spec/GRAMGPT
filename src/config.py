from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    bot_token: Optional[str] = None
    openai_api_key: Optional[str] = None

    # Models
    model_name: str = "gpt-4o"
    image_model: str = "dall-e-3"
    whisper_model: str = "whisper-1"

    # Parameters
    temperature: float = 0.7
    max_tokens: int = 2000

    # GPTGRAM Ultimate Specific
    human_emulation_enabled: bool = True
    anti_ban_risk_threshold: int = 80
    proxy_list_path: str = "proxies.txt"

    system_prompt: str = (
        "Вы — GRAMGPT, продвинутая ИИ-система для автоматизации и маркетинга в Telegram. "
        "Ваша цель — быть максимально полезным, отвечать на вопросы пользователя точно и профессионально. "
        "Отвечайте на языке пользователя. Будьте кратки и информативны."
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
