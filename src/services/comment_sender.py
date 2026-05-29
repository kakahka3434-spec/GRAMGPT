"""
Advanced Comment Sender - GRAMGPT Premium Commenting Engine.

Features:
- 3 comment styles: engaging, expert, casual
- Sentiment analysis + style adaptation
- Behavioral anti-ban patterns (read → think → send)
- Contextual memory (no duplicate comments)
- Detailed logging for transparency
"""

import asyncio
import hashlib
import logging
import random
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple

from telethon.errors import FloodWaitError

from src.core.ai_client import ai_client
from src.db.comment_memory import comment_memory

logger = logging.getLogger(__name__)


class CommentSender:
    """
    Premium comment automation with anti-ban protection and style diversity.
    """
    
    # Style definitions with prompts
    STYLE_PROMPTS = {
        "expert": {
            "description": "экспертный, профессиональный",
            "instruction": """Ты — эксперт в теме поста. Твой комментарий должен:
- Добавить ценный инсайт или факт по теме
- Быть лаконичным (1-2 предложения)
- Использовать профессиональный, но не сухой тон
- Не использовать эмодзи
- Не задавать риторических вопросов

Только текст комментария, без объяснений."""
        },
        "engaging": {
            "description": "вовлекающий, провоцирующий дискуссию",
            "instruction": """Ты — активный участник дискуссии. Твой комментарий должен:
- Выразить эмоцию по поводу поста (удивление/согласие/вопрос)
- Задать открытый вопрос, который провоцирует обсуждение
- Использовать ровно 1 эмодзи для акцента
- Быть коротким (не более 2 предложений)

Только текст комментария, без объяснений."""
        },
        "casual": {
            "description": "неформальный, дружеский",
            "instruction": """Ты — обычный пользователь, который зашёл почитать. Твой комментарий должен:
- Быть максимально естественным, как в жизни
- Можно использовать сленг, сокращения, юмор
- 0-2 эмодзи, но только если уместно
- 1 предложение, не больше

Только текст комментария, без объяснений."""
        },
        "balanced": {
            "description": "сбалансированный",
            "instruction": """Ты — участник телеграм-канала. Напиши естественный комментарий:
- 1-2 предложения
- Можно использовать 1 эмодзи
- Будь дружелюбным и заинтересованным

Только текст комментария."""
        }
    }
    
    # Anti-ban behavioral patterns (seconds)
    DELAY_PATTERNS = {
        "read": (3, 8),        # "прочитал пост"
        "think": (2, 5),       # "обдумываю ответ"
        "type": (5, 15),       # "печатаю комментарий"
        "pause_after": (30, 120)  # "отдохнул, пошёл дальше"
    }
    
    def __init__(self, telegram_client, ai_client_instance=None, hours_between_comments: int = 24):
        """
        Initialize CommentSender.
        
        Args:
            telegram_client: TelegramUserClient instance
            ai_client_instance: AIClient instance (optional, uses global if None)
            hours_between_comments: Minimum hours before re-commenting same post
        """
        self.telegram = telegram_client
        self.ai = ai_client_instance or ai_client
        self.hours_between = hours_between_comments
        
        logger.info(f"🎯 CommentSender initialized (anti-ban: {hours_between_comments}h cooldown)")
    
    async def _human_like_delay(self, action: str) -> float:
        """Generate realistic delay for behavioral pattern."""
        min_s, max_s = self.DELAY_PATTERNS.get(action, (5, 15))
        delay = random.uniform(min_s, max_s)
        
        logger.debug(f"⏳ [pattern] {action}: {delay:.1f}s")
        await asyncio.sleep(delay)
        return delay
    
    def _analyze_sentiment(self, text: str) -> str:
        """
        Simple sentiment analysis for post adaptation.
        Returns: positive, negative, neutral
        """
        text_lower = text.lower()
        
        positive_words = ['👍', '❤️', '🔥', '🚀', '💪', 'отлично', 'круто', 'супер', 'лучший', 'победа', 'успех', 'рост', 'плюс']
        negative_words = ['👎', '💔', '😞', 'плохо', 'ужас', 'кризис', 'падение', 'проблема', 'минус', 'ошибка', 'провал']
        
        pos_count = sum(1 for w in positive_words if w in text_lower)
        neg_count = sum(1 for w in negative_words if w in text_lower)
        
        if pos_count > neg_count:
            return "positive"
        elif neg_count > pos_count:
            return "negative"
        return "neutral"
    
    def _build_prompt(self, post_text: str, style: str, sentiment: str) -> str:
        """Build dynamic prompt based on style and sentiment."""
        style_config = self.STYLE_PROMPTS.get(style, self.STYLE_PROMPTS["balanced"])
        
        sentiment_adaptation = {
            "positive": "Пост в позитивном ключе — отреагируй с энтузиазмом.",
            "negative": "Пост о проблеме/негативе — будь конструктивным, не добавляй негатива.",
            "neutral": "Пост нейтральный — дай нейтральную реакцию."
        }.get(sentiment, "")
        
        prompt = f"""{style_config['instruction']}

Тональность поста: {sentiment_adaptation}

Пост для анализа:
"{post_text[:400]}"

Напиши уникальный комментарий (1-2 предложения), который будет отличаться от типичных реакций. Не используй банальные фразы вроде "согласен", "интересно", "спасибо за пост".

Только текст комментария:"""
        
        return prompt
    
    async def generate_comment(
        self, 
        post_text: str, 
        style: str = "balanced",
        context: Optional[Dict] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generate AI comment with style and sentiment adaptation.
        
        Returns:
            Tuple of (comment_text, metadata)
        """
        start_time = time.time()
        
        # Analyze sentiment
        sentiment = self._analyze_sentiment(post_text)
        
        # Build prompt
        prompt = self._build_prompt(post_text, style, sentiment)
        
        logger.info(f"🎨 [style] {style} | Тональность: {sentiment} | Промпт: {len(prompt)} chars")
        
        # Generate with AI
        messages = [{"role": "user", "content": prompt}]
        
        try:
            response = await self.ai.get_chat_response(0, messages)
            
            # If AI returned an error message, fall back to template
            if response.startswith("❌"):
                raise Exception(response)
            
            # Clean up response
            comment = response.strip().strip('"').strip("'")
            
            # Remove common prefixes
            prefixes = ["Комментарий:", "Ответ:", "Comment:", "Коммент:"]
            for prefix in prefixes:
                if comment.lower().startswith(prefix.lower()):
                    comment = comment[len(prefix):].strip()
            
            metadata = {
                "style": style,
                "sentiment": sentiment,
                "prompt_length": len(prompt),
                "response_length": len(comment),
                "generation_time": round(time.time() - start_time, 2)
            }
            
            logger.info(f"🤖 [generate] Готово за {metadata['generation_time']}s | Длина: {metadata['response_length']} chars")
            
            return comment, metadata
            
        except Exception as e:
            logger.error(f"❌ [generate] Ошибка генерации: {e}")
            # Fallback to simple comment
            fallback = "Интересная информация, спасибо за分享!"
            return fallback, {"style": style, "sentiment": sentiment, "error": str(e), "fallback": True}
    
    async def send_comment(
        self,
        channel: str,
        message_id: int,
        comment_text: str,
        simulate_reading: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Send comment with behavioral anti-ban simulation.
        
        Args:
            channel: Channel username
            message_id: Post ID
            comment_text: Comment text
            simulate_reading: Add human-like delays before sending
        
        Returns:
            Comment info dict or None on failure
        """
        if not self.telegram._is_connected:
            logger.error("❌ [send] Telegram client not connected")
            return None
        
        logger.info(f"📨 [send] Подготовка комментария к @{channel} #{message_id}")
        
        try:
            # Anti-ban: behavioral pattern
            if simulate_reading:
                logger.info("⏳ [pattern] Эмуляция чтения...")
                await self._human_like_delay("read")
                
                logger.info("⏳ [pattern] Эмуляция размышления...")
                await self._human_like_delay("think")
                
                logger.info("⏳ [pattern] Эмуляция печати...")
                await self._human_like_delay("type")
            
            # Send comment
            start_time = time.time()
            result = await self.telegram.send_comment(channel, message_id, comment_text)
            
            if result:
                send_time = round(time.time() - start_time, 2)
                logger.info(f"💬 [sent] @{channel} #{message_id} | ID: {result['id']} | Затрачено: {send_time}s")
                
                # Anti-ban: pause after
                if simulate_reading:
                    pause = random.uniform(*self.DELAY_PATTERNS["pause_after"])
                    logger.info(f"⏳ [pattern] Пауза после: {pause:.1f}s")
                    await asyncio.sleep(pause)
                
                return result
            else:
                logger.error(f"❌ [send] Не удалось отправить комментарий")
                return None
                
        except FloodWaitError as e:
            logger.error(f"🚫 [send] Flood wait: {e.seconds}s")
            return None
        except Exception as e:
            logger.error(f"❌ [send] Ошибка: {e}")
            return None
    
    async def comment_with_full_cycle(
        self,
        channel: str,
        post_id: int,
        post_text: str,
        style: str = "balanced"
    ) -> Optional[Dict[str, Any]]:
        """
        Full advanced commenting cycle:
        1. Check memory (skip if already commented)
        2. Generate comment with style/sentiment
        3. Send with behavioral patterns
        4. Record to memory
        
        Returns:
            Result dict with full cycle info or None
        """
        cycle_start = time.time()
        
        # Step 1: Check memory
        if comment_memory.is_already_commented(channel, post_id, self.hours_between):
            logger.info(f"🧠 [memory] Пропуск: @{channel} #{post_id} уже комментировали")
            return None
        
        # Step 2: Generate comment
        comment_text, gen_metadata = await self.generate_comment(post_text, style)
        
        # Step 3: Send with anti-ban
        send_result = await self.send_comment(channel, post_id, comment_text, simulate_reading=True)
        
        if not send_result:
            return None
        
        # Step 4: Record to memory
        comment_memory.record_comment(channel, post_id, style, comment_text[:100])
        
        # Calculate total time
        total_time = round(time.time() - cycle_start, 1)
        
        result = {
            "success": True,
            "channel": channel,
            "post_id": post_id,
            "comment_id": send_result["id"],
            "comment_text": comment_text,
            "style": style,
            "sentiment": gen_metadata.get("sentiment", "unknown"),
            "generation_time": gen_metadata.get("generation_time", 0),
            "total_time": total_time
        }
        
        logger.info(f"✅ [cycle] Завершено за {total_time}s | @{channel} #{post_id} | style: {style}")
        
        return result
    
    async def batch_comment(
        self,
        channel: str,
        posts: list,
        style: str = "balanced",
        max_comments: int = 3
    ) -> list:
        """
        Process multiple posts with memory check and delays.
        
        Args:
            channel: Channel username
            posts: List of post dicts with 'id' and 'text'
            style: Comment style
            max_comments: Maximum comments to send
        
        Returns:
            List of successful comment results
        """
        results = []
        
        logger.info(f"🔄 [batch] Начало обработки {len(posts)} постов из @{channel}")
        
        for i, post in enumerate(posts[:max_comments]):
            if i > 0:
                # Delay between posts
                delay = random.uniform(60, 180)
                logger.info(f"⏳ [batch] Пауза между постами: {delay:.1f}s")
                await asyncio.sleep(delay)
            
            result = await self.comment_with_full_cycle(
                channel=channel,
                post_id=post["id"],
                post_text=post.get("text", ""),
                style=style
            )
            
            if result:
                results.append(result)
        
        logger.info(f"✅ [batch] Завершено: {len(results)}/{len(posts[:max_comments])} комментариев")
        
        return results
