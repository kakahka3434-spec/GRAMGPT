from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    bot_token: Optional[str] = None

    # AI Provider settings
    ai_provider: str = "openai"
    openai_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None

    # Telegram User API credentials (Telethon)
    telegram_api_id: Optional[int] = None
    telegram_api_hash: Optional[str] = None
    telegram_phone: Optional[str] = None

    # Models
    model_name: str = "gpt-4o"
    image_model: str = "dall-e-3"
    whisper_model: str = "whisper-1"

    # Parameters
    temperature: float = 0.7
    max_tokens: int = 2000

    # GRAMGPT Specific
    human_emulation_enabled: bool = True
    anti_ban_risk_threshold: int = 80
    proxy_list_path: str = "proxies.txt"

    system_prompt: str = (
        "Вы — GRAMGPT, продвинутая ИИ-система для автоматизации и маркетинга в Telegram. "
        "Ваша цель — быть максимально полезным, отвечать на вопросы пользователя точно и профессионально. "
        "Отвечайте на языке пользователя. Будьте кратки и информативны."
    )

    # Redis / Celery
    redis_password: Optional[str] = None
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"
    celery_task_always_eager: bool = False

    model_config = SettingsConfigDict(
        env_file=(".env.local", ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
