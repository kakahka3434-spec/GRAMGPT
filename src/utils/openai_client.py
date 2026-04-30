from typing import List, Dict
from openai import AsyncOpenAI
from src.config import settings

class OpenAIClient:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def get_chat_response(self, messages: List[Dict[str, str]]) -> str:
        try:
            # Prepend system prompt
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
            return f"Error communicating with OpenAI: {e}"

openai_client = OpenAIClient()
