from typing import List, Dict, Optional
from openai import AsyncOpenAI
from src.config import settings
from src.utils.local_engine import local_engine

class OpenAIClient:
    def __init__(self):
        self.api_enabled = bool(settings.openai_api_key)
        if self.api_enabled:
            self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def get_chat_response(self, messages: List[Dict[str, any]]) -> str:
        if not self.api_enabled:
            # Fallback logic
            last_msg = messages[-1].get("content", "")
            if isinstance(last_msg, list): # handle multi-modal format
                last_msg = last_msg[0].get("text", "")

            if "стратег" in last_msg.lower() or "анализ" in last_msg.lower():
                return local_engine.get_strategy_response(last_msg)
            return local_engine.get_chat_response()

        try:
            full_messages = [{"role": "system", "content": settings.system_prompt}] + messages
            response = await self.client.chat.completions.create(
                model=settings.model_name,
                messages=full_messages,
                temperature=settings.temperature,
                max_tokens=settings.max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"❌ Ошибка ИИ: {e}"

    async def generate_image(self, prompt: str) -> str:
        if not self.api_enabled:
            return "❌ API ключ отсутствует. Генерация изображений недоступна."
        try:
            response = await self.client.images.generate(model=settings.image_model, prompt=prompt)
            return response.data[0].url
        except Exception as e:
            return f"❌ Ошибка генерации: {e}"

    async def transcribe_voice(self, file_path: str) -> str:
        if not self.api_enabled:
            return "❌ API ключ отсутствует. Транскрипция голоса недоступна."
        try:
            with open(file_path, "rb") as audio_file:
                transcript = await self.client.audio.transcriptions.create(model=settings.whisper_model, file=audio_file)
            return transcript.text
        except Exception as e:
            return f"❌ Ошибка транскрипции: {e}"

openai_client = OpenAIClient()
