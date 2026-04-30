from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    bot_token: Optional[str] = None
    openai_api_key: Optional[str] = None
    model_name: str = "gpt-4-turbo"
    temperature: float = 0.7
    max_tokens: int = 1000
    system_prompt: str = "You are a helpful assistant. You answer concisely and professionally."

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
