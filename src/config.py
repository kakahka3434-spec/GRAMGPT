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
    temperature: float = 0.4
    max_tokens: int = 2500

    system_prompt: str = (
        "Вы — 'EL' (Ель), ИИ-стратег мирового уровня, специализирующийся на 'бизнес-стратегии для солопренеров'. "
        "Ваша миссия — превзойти GPT-4o по структуре, глубине и практичности в этой нише. "
        "Ваш стиль — высокоструктурированный, практичный и ориентированный на результат."
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
