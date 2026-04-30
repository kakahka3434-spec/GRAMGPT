from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    bot_token: Optional[str] = None
    openai_api_key: Optional[str] = None

    # Models
    model_name: str = "gpt-4o"  # Use gpt-4o for vision and speed
    image_model: str = "dall-e-3"
    whisper_model: str = "whisper-1"

    # Parameters
    temperature: float = 0.7
    max_tokens: int = 1500
    system_prompt: str = (
        "You are GRAMGPT, a highly advanced AI assistant. "
        "You provide helpful, creative, and professional responses. "
        "You can analyze images, generate images, and understand voice messages."
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
