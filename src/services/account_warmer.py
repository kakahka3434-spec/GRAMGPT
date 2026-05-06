"""
Account Warmer - Human behavior simulation for anti-ban protection.
Simulates realistic Telegram usage patterns: reading, reactions, scrolling.
"""

import asyncio
import logging
import random
from typing import Optional, List
from datetime import datetime

from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import SendReactionRequest
from telethon.errors import FloodWaitError, UserAlreadyParticipantError

from src.core.rate_limiter import AdaptiveRateLimiter

logger = logging.getLogger(__name__)


class AccountWarmer:
    """
    Simulates human-like activity to warm up accounts and avoid bans.
    Includes: scrolling, reactions, subscriptions, reading patterns.
    """
    
    # Popular channels for random subscriptions (safe, public, active)
    WARMUP_CHANNELS = [
        "durov", "telegram", "cryptonews", "techcrunch", 
        "theguardian", "wsj", "reuters", "bloomberg",
        "github", "producthunt", "hackernews"
    ]
    
    # Reaction emojis pool
    REACTION_EMOJIS = ["👍", "❤️", "🔥", "👏", "😊", "🤔", "😮", "💯"]
    
    def __init__(self, telegram_client, settings=None):
        """
        Initialize AccountWarmer.
        
        Args:
            telegram_client: TelegramUserClient instance
            settings: Optional settings dict
        """
        self.telegram = telegram_client
        self.settings = settings or {}
        self.rate_limiter = AdaptiveRateLimiter()
        self._warmup_task = None
        self._is_warming = False
        
        logger.info("🧼 AccountWarmer initialized")
    
    async def _human_like_delay(self, action: str = "read") -> float:
        """
        Generate human-like delay for specific action.
        
        Patterns:
        - read: 3-8s (reading text)
        - view: 5-15s (viewing media)
        - scroll: 1-4s (scrolling between posts)
        - decide: 2-5s (deciding to react)
        - click: 0.5-2s (clicking a button)
        """
        patterns = {
            "read": (3, 8),
            "view": (5, 15),
            "scroll": (1, 4),
            "decide": (2, 5),
            "click": (0.5, 2),
            "pause": (10, 30)
        }
        
        min_s, max_s = patterns.get(action, (2, 5))
        delay = random.uniform(min_s, max_s)
        
        logger.debug(f"⏳ [warming] {action}: {delay:.1f}s")
        await asyncio.sleep(delay)
        return delay
    
    async def random_scroll(self, channel: str, posts: int = 5) -> None:
        """
        Simulate reading/scrolling through a channel.
        
        Args:
            channel: Channel username
            posts: Number of posts to "read"
        """
        if not self.telegram._is_connected:
            logger.warning("🧼 [warming] Not connected, skipping scroll")
            return
        
        logger.info(f"🧼 [warming] Scrolling through @{channel}, {posts} posts")
        
        try:
            # Get recent messages
            messages = await self.telegram.parse_last_messages(channel, limit=posts)
            
            if not messages:
                logger.warning(f"🧼 [warming] No messages found in @{channel}")
                return
            
            for i, msg in enumerate(messages):
                # Simulate reading the post
                read_time = await self._human_like_delay("read")
                
                # Log what we "read"
                preview = msg['text'][:60].replace('\n', ' ') if msg['text'] else "(media)"
                logger.info(f"🧼 [warming] Read post {msg['id']}: \"{preview}...\" ({read_time:.1f}s)")
                
                # Sometimes pause between posts
                if random.random() > 0.7 and i < len(messages) - 1:
                    await self._human_like_delay("pause")
                
                # Scroll to next
                if i < len(messages) - 1:
                    await self._human_like_delay("scroll")
            
            logger.info(f"✅ [warming] Scrolled through {len(messages)} posts in @{channel}")
            
        except Exception as e:
            logger.error(f"❌ [warming] Scroll error: {e}")
    
    async def safe_react(self, channel: str, post_id: int, emoji: Optional[str] = None) -> bool:
        """
        Safely add a reaction to a post.
        
        Args:
            channel: Channel username
            post_id: Post ID
            emoji: Emoji to use (random if None)
        
        Returns:
            True if reaction added successfully
        """
        if not self.telegram._is_connected:
            logger.warning("🧼 [warming] Not connected, skipping reaction")
            return False
        
        emoji = emoji or random.choice(self.REACTION_EMOJIS)
        
        try:
            logger.info(f"🧼 [warming] Reacting to @{channel} #{post_id} with {emoji}")
            
            # Decision delay
            await self._human_like_delay("decide")
            
            # Get channel entity
            entity = await self.telegram._client.get_entity(channel)
            
            # Send reaction using Telethon
            await self.telegram._client(SendReactionRequest(
                peer=entity,
                msg_id=post_id,
                reaction=[emoji]
            ))
            
            # Click delay
            await self._human_like_delay("click")
            
            logger.info(f"✅ [warming] Reacted with {emoji}")
            self.rate_limiter.record_success("reaction")
            return True
            
        except FloodWaitError as e:
            logger.warning(f"🚫 [warming] Flood wait on reaction: {e.seconds}s")
            self.rate_limiter.record_flood_wait(e.seconds)
            return False
        except Exception as e:
            logger.error(f"❌ [warming] Reaction failed: {e}")
            return False
    
    async def safe_join_channel(self, channel: str) -> bool:
        """
        Safely join a public channel.
        
        Args:
            channel: Channel username
        
        Returns:
            True if joined successfully
        """
        if not self.telegram._is_connected:
            logger.warning("🧼 [warming] Not connected, skipping join")
            return False
        
        try:
            logger.info(f"🧼 [warming] Joining channel @{channel}")
            
            # Get entity
            entity = await self.telegram._client.get_entity(channel)
            
            # Check if already member
            try:
                await self.telegram._client(JoinChannelRequest(channel=entity))
                logger.info(f"✅ [warming] Joined @{channel}")
                self.rate_limiter.record_success("subscribe")
                return True
            except UserAlreadyParticipantError:
                logger.info(f"ℹ️ [warming] Already in @{channel}")
                return True
                
        except FloodWaitError as e:
            logger.warning(f"🚫 [warming] Flood wait on join: {e.seconds}s")
            self.rate_limiter.record_flood_wait(e.seconds)
            return False
        except Exception as e:
            logger.error(f"❌ [warming] Join failed: {e}")
            return False
    
    async def warm_up_session(self, duration_minutes: int = 15) -> bool:
        """
        Full warmup cycle - simulates realistic user session.
        
        Args:
            duration_minutes: How long to simulate activity
        
        Returns:
            True if warmup completed
        """
        if self._is_warming:
            logger.warning("🧼 [warming] Already warming up, skipping")
            return False
        
        self._is_warming = True
        start_time = datetime.now()
        
        try:
            logger.info(f"🧼 [warming] Starting warmup session ({duration_minutes}min)")
            
            # 1. Random scroll through popular channels
            channels_to_scroll = random.sample(self.WARMUP_CHANNELS, min(3, len(self.WARMUP_CHANNELS)))
            for channel in channels_to_scroll:
                await self.random_scroll(channel, posts=random.randint(3, 8))
                
                # Delay between channels
                await asyncio.sleep(random.uniform(5, 15))
            
            # 2. Add 1-2 reactions on random posts
            if random.random() > 0.3:
                reaction_channel = random.choice(channels_to_scroll)
                messages = await self.telegram.parse_last_messages(reaction_channel, limit=5)
                if messages:
                    target_msg = random.choice(messages)
                    await self.safe_react(reaction_channel, target_msg['id'])
            
            # 3. Maybe join a new channel (30% chance)
            if random.random() > 0.7:
                new_channel = random.choice([c for c in self.WARMUP_CHANNELS if c not in channels_to_scroll])
                await self.safe_join_channel(new_channel)
            
            elapsed = (datetime.now() - start_time).total_seconds() / 60
            logger.info(f"✅ [warming] Session completed: {elapsed:.1f}min activity simulated")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ [warming] Session error: {e}")
            return False
        finally:
            self._is_warming = False
    
    async def run_background_warmup(self, interval_hours: float = 4.0) -> None:
        """
        Run periodic warmup in background.
        
        Args:
            interval_hours: How often to run warmup (in hours)
        """
        logger.info(f"🔄 [warming] Background warmup started (every {interval_hours}h)")
        
        while True:
            try:
                await self.warm_up_session(duration_minutes=random.randint(10, 20))
                
                # Wait for next interval
                wait_seconds = interval_hours * 3600
                logger.info(f"⏰ [warming] Next warmup in {interval_hours}h")
                await asyncio.sleep(wait_seconds)
                
            except asyncio.CancelledError:
                logger.info("🛑 [warming] Background warmup cancelled")
                break
            except Exception as e:
                logger.error(f"❌ [warming] Background error: {e}")
                await asyncio.sleep(600)  # Wait 10min on error
    
    async def stop(self) -> None:
        """Stop warmup activities."""
        self._is_warming = False
        if self._warmup_task:
            self._warmup_task.cancel()
            try:
                await self._warmup_task
            except asyncio.CancelledError:
                pass
        logger.info("🛑 [warming] Warmer stopped")
    
    def get_status(self) -> dict:
        """Get current warmer status."""
        return {
            "is_warming": self._is_warming,
            "rate_limiter": self.rate_limiter.get_status()
        }
