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

    system_prompt: str = (
        "Вы — GRAMGPT, продвинутый ИИ-ассистент. "
        "Вы помогаете пользователям в чате, анализируете изображения и голос, генерируете картинки. "
        "Отвечайте профессионально и дружелюбно на русском языке."
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
