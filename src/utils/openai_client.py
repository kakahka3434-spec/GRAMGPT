import base64
from typing import List, Dict, Optional
from openai import AsyncOpenAI
from src.config import settings

class OpenAIClient:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def get_chat_response(self, messages: List[Dict[str, any]]) -> str:
        try:
            full_messages = [
                {"role": "system", "content": settings.system_prompt}
            ] + messages

            response = await self.client.chat.completions.create(
                model=settings.model_name,
                messages=full_messages,
                temperature=settings.temperature,
                max_tokens=settings.max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"❌ Error communicating with OpenAI: {e}"

    async def generate_image(self, prompt: str) -> str:
        try:
            response = await self.client.images.generate(
                model=settings.image_model,
                prompt=prompt,
                n=1,
                size="1024x1024"
            )
            return response.data[0].url
        except Exception as e:
            return f"❌ Error generating image: {e}"

    async def transcribe_voice(self, file_path: str) -> str:
        try:
            with open(file_path, "rb") as audio_file:
                transcript = await self.client.audio.transcriptions.create(
                    model=settings.whisper_model,
                    file=audio_file
                )
            return transcript.text
        except Exception as e:
            return f"❌ Error transcribing voice: {e}"

openai_client = OpenAIClient()
