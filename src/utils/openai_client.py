from openai import AsyncOpenAI
from src.config import settings

class OpenAIClient:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def get_chat_response(self, message: str, system_prompt: str = "You are a helpful assistant.") -> str:
        try:
            response = await self.client.chat.completions.create(
                model=settings.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error communicating with OpenAI: {e}"

openai_client = OpenAIClient()
