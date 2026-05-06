"""
Universal AI Client supporting OpenAI, OpenRouter (free tier), and Groq.
"""

from typing import List, Dict, Optional
import logging
from openai import AsyncOpenAI
from src.config import settings
from src.db.database import db

logger = logging.getLogger(__name__)


class AIClient:
    """
    Unified AI client supporting multiple providers:
    - OpenAI (paid)
    - OpenRouter (free tier available: https://openrouter.ai/)
    - Groq (free tier available: https://groq.com/)
    """
    
    def __init__(self):
        self.client = None
        self.provider = settings.ai_provider.lower()
        self.base_url = None
        self.api_key = None
        
        # Configure based on provider
        if self.provider == "openrouter":
            self.api_key = settings.openrouter_api_key
            self.base_url = "https://openrouter.ai/api/v1"
            self._init_client()
            logger.info("AI Client initialized with OpenRouter")
            
        elif self.provider == "groq":
            self.api_key = settings.groq_api_key
            self.base_url = "https://api.groq.com/openai/v1"
            self._init_client()
            logger.info("AI Client initialized with Groq")
            
        elif self.provider == "openai":
            self.api_key = settings.openai_api_key
            self._init_client()
            logger.info("AI Client initialized with OpenAI")
        else:
            logger.warning(f"Unknown AI provider: {self.provider}. AI features disabled.")
    
    def _init_client(self):
        """Initialize the OpenAI-compatible client."""
        self.is_available = False  # Default to unavailable
        if self.api_key:
            try:
                kwargs = {"api_key": self.api_key}
                if self.base_url:
                    kwargs["base_url"] = self.base_url
                self.client = AsyncOpenAI(**kwargs)
                self.is_available = True
                logger.info(f"AI client initialized and available ({self.provider})")
            except Exception as e:
                logger.error(f"Failed to initialize AI client: {e}")
                self.is_available = False
        else:
            logger.warning(f"No API key configured for provider: {self.provider}")
            self.is_available = False
    
    async def get_chat_response(self, chat_id: int, messages: List[Dict[str, any]]) -> str:
        """
        Get chat response from the configured AI provider.
        
        Args:
            chat_id: Telegram chat ID for user settings
            messages: List of message dicts with 'role' and 'content'
        
        Returns:
            Response text or error message
        """
        if not self.client:
            return f"❌ API ключ не настроен ({self.provider}). Добавьте ключ в .env.local"
        
        # Get user's preferred model or use default
        try:
            user_model = db.get_user_model(chat_id) if hasattr(db, 'get_user_model') else settings.model_name
        except:
            user_model = settings.model_name
        
        try:
            full_messages = [{"role": "system", "content": settings.system_prompt}] + messages
            
            # Add headers for OpenRouter
            extra_headers = {}
            if self.provider == "openrouter":
                extra_headers = {
                    "HTTP-Referer": "https://gptgram.app",
                    "X-Title": "GRAMGPT"
                }
            
            response = await self.client.chat.completions.create(
                model=user_model,
                messages=full_messages,
                temperature=settings.temperature,
                max_tokens=settings.max_tokens,
                extra_headers=extra_headers if extra_headers else None
            )
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"AI Chat Error ({self.provider}): {e}")
            return f"❌ Ошибка ИИ ({self.provider}): {str(e)}"
    
    async def generate_image(self, prompt: str) -> str:
        """
        Generate image using DALL-E (OpenAI only).
        Free alternatives don't support image generation.
        """
        if not self.client:
            return "❌ API клиент не инициализирован."
        
        if self.provider != "openai":
            return "⚠️ Генерация изображений доступна только через OpenAI. Используйте OpenAI для этой функции."
        
        try:
            response = await self.client.images.generate(
                model=settings.image_model,
                prompt=prompt,
                quality="standard",
                n=1
            )
            return response.data[0].url
        except Exception as e:
            logger.error(f"Image Generation Error: {e}")
            return f"❌ Ошибка генерации изображения: {str(e)}"
    
    async def transcribe_voice(self, file_path: str) -> str:
        """
        Transcribe voice using Whisper (OpenAI only).
        Free alternatives don't support voice transcription.
        """
        if not self.client:
            return "❌ API клиент не инициализирован."
        
        if self.provider != "openai":
            return "⚠️ Распознавание голоса доступно только через OpenAI."
        
        try:
            with open(file_path, "rb") as audio_file:
                transcript = await self.client.audio.transcriptions.create(
                    model=settings.whisper_model,
                    file=audio_file
                )
            return transcript.text
        except Exception as e:
            logger.error(f"Whisper Error: {e}")
            return f"❌ Ошибка распознавания речи: {str(e)}"


# Global instance
ai_client = AIClient()
