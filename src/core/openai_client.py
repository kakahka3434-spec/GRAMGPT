from typing import List, Dict, Optional
import logging
from openai import AsyncOpenAI
from src.config import settings
from src.db.database import db

logger = logging.getLogger(__name__)

class OpenAIClient:
    def __init__(self):
        self.client = None
        if settings.openai_api_key:
            try:
                self.client = AsyncOpenAI(api_key=settings.openai_api_key)
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")

    async def get_chat_response(self, chat_id: int, messages: List[Dict[str, any]]) -> str:
        if not self.client:
            return "❌ API ключ OpenAI не настроен или невалиден. Пожалуйста, проверьте переменные окружения."

        user_model = db.get_user_model(chat_id)

        try:
            full_messages = [{"role": "system", "content": settings.system_prompt}] + messages
            response = await self.client.chat.completions.create(
                model=user_model,
                messages=full_messages,
                temperature=settings.temperature,
                max_tokens=settings.max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI Chat Error: {e}")
            return f"❌ Произошла ошибка при общении с ИИ: {str(e)}"

    async def generate_image(self, prompt: str) -> str:
        if not self.client:
            return "❌ API ключ OpenAI не настроен."
        try:
            response = await self.client.images.generate(
                model=settings.image_model,
                prompt=prompt,
                quality="standard",
                n=1
            )
            return response.data[0].url
        except Exception as e:
            logger.error(f"OpenAI Image Error: {e}")
            return f"❌ Ошибка генерации изображения: {str(e)}"

    async def transcribe_voice(self, file_path: str) -> str:
        if not self.client:
            return "❌ API ключ OpenAI не настроен."
        try:
            with open(file_path, "rb") as audio_file:
                transcript = await self.client.audio.transcriptions.create(
                    model=settings.whisper_model,
                    file=audio_file
                )
            return transcript.text
        except Exception as e:
            logger.error(f"OpenAI Whisper Error: {e}")
            return f"❌ Ошибка распознавания речи: {str(e)}"

openai_client = OpenAIClient()
