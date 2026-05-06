"""
Comment Sniper - Immediate emoji comments + delayed promo edit.
Captures first comment position and replaces it with promo text later.
"""

import asyncio
import logging
import sqlite3
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Callable, Any
from dataclasses import dataclass

from telethon import events
from telethon.tl.types import Message, Channel

logger = logging.getLogger(__name__)


@dataclass
class PendingEdit:
    """Represents a comment queued for editing."""
    channel: str
    post_id: int
    emoji_msg_id: int
    created_at: datetime
    edit_after: int  # seconds
    target_link: str
    post_text: str


class CommentSniper:
    """
    Sniper strategy: Fast emoji → delayed promo edit.
    Monitors channels, posts emoji immediately, edits to promo later.
    """
    
    # Emoji pool for first comments
    EMOJI_COMMENTS = ["👍", "🔥", "👏", "💯", "🎯", "✅", "🚀", "💪"]
    
    def __init__(
        self,
        telegram_client,
        promo_engine,
        settings: Optional[Dict] = None
    ):
        """
        Initialize CommentSniper.
        
        Args:
            telegram_client: Connected TelegramUserClient
            promo_engine: PromoEngine instance for generating promo text
            settings: Configuration dict with delays, limits
        """
        self.client = telegram_client
        self.promo_engine = promo_engine
        self.settings = settings or {}
        
        # Edit queue and worker
        self.pending_edits: asyncio.Queue[PendingEdit] = asyncio.Queue()
        self._edit_task: Optional[asyncio.Task] = None
        self._monitoring = False
        self._handlers = []
        
        # Stats
        self.stats = {
            "emoji_sent": 0,
            "edits_completed": 0,
            "edits_failed": 0,
            "posts_seen": 0
        }
        
        # Callbacks for integration
        self.on_emoji_sent: Optional[Callable] = None
        self.on_edit_complete: Optional[Callable] = None
        
        logger.info("🎯 CommentSniper initialized")
    
    async def start_monitoring(
        self,
        channels: List[str],
        edit_delay_range: tuple = (180, 300),
        target_link: str = ""
    ) -> None:
        """
        Start monitoring channels for new posts.
        
        Args:
            channels: List of channel usernames to monitor
            edit_delay_range: (min, max) seconds before editing to promo
            target_link: Link to insert in promo comments
        """
        if self._monitoring:
            logger.warning("🎯 Already monitoring")
            return
        
        self._monitoring = True
        logger.info(f"🎯 Starting sniper on {len(channels)} channels")
        
        # Get channel entities
        channel_entities = []
        for username in channels:
            try:
                entity = await self.client.client.get_entity(username)
                channel_entities.append((username, entity))
                logger.info(f"   📡 Monitoring: @{username}")
            except Exception as e:
                logger.warning(f"⚠️ Cannot monitor @{username}: {e}")
        
        # Set up handlers for each channel
        for username, entity in channel_entities:
            handler = self.client.client.add_event_handler(
                self._on_new_message,
                events.NewMessage(chats=entity)
            )
            self._handlers.append((username, handler))
        
        # Start edit worker
        self._edit_task = asyncio.create_task(self._edit_worker())
        
        logger.info("🎯 Sniper active - waiting for new posts")
    
    async def stop_monitoring(self) -> None:
        """Stop monitoring and cleanup."""
        if not self._monitoring:
            return
        
        logger.info("🛑 Stopping CommentSniper...")
        self._monitoring = False
        
        # Remove handlers
        for username, handler in self._handlers:
            self.client.client.remove_event_handler(handler)
            logger.debug(f"   Removed handler for @{username}")
        
        self._handlers.clear()
        
        # Cancel edit worker
        if self._edit_task:
            self._edit_task.cancel()
            try:
                await self._edit_task
            except asyncio.CancelledError:
                pass
        
        logger.info("🛑 CommentSniper stopped")
    
    async def _on_new_message(self, event: events.NewMessage.Event) -> None:
        """Handle new post in monitored channel."""
        if not self._monitoring:
            return
        
        try:
            message = event.message
            
            # Only handle channel posts (not comments, not forwards from bots)
            if not message.post:
                return
            
            # Get channel info
            chat = await event.get_chat()
            if not isinstance(chat, Channel):
                return
            
            channel_username = chat.username
            post_id = message.id
            
            self.stats["posts_seen"] += 1
            
            logger.info(f"🎯 [SNIPER] New post in @{channel_username}: #{post_id}")
            
            # Wait 1-3 seconds before commenting (avoid instant bot-like speed)
            await asyncio.sleep(random.uniform(1, 3))
            
            # Send emoji comment immediately
            emoji = self._get_random_emoji()
            result = await self._send_emoji_comment(channel_username, post_id, emoji)
            
            if result:
                emoji_msg_id = result["message_id"]
                self.stats["emoji_sent"] += 1
                
                logger.info(f"✅ [SNIPER] Emoji sent: {emoji} (msg_id: {emoji_msg_id})")
                
                # Queue for editing
                edit_delay = random.randint(
                    self.settings.get("edit_delay_min", 180),
                    self.settings.get("edit_delay_max", 300)
                )
                
                pending = PendingEdit(
                    channel=channel_username,
                    post_id=post_id,
                    emoji_msg_id=emoji_msg_id,
                    created_at=datetime.now(),
                    edit_after=edit_delay,
                    target_link=self.settings.get("target_link", ""),
                    post_text=message.message or ""
                )
                
                await self.pending_edits.put(pending)
                
                logger.info(f"⏳ [SNIPER] Queued for edit in {edit_delay}s")
                
                # Callback
                if self.on_emoji_sent:
                    await self.on_emoji_sent(pending)
            else:
                logger.warning(f"❌ [SNIPER] Failed to send emoji to @{channel_username}:{post_id}")
                
        except Exception as e:
            logger.error(f"❌ [SNIPER] Error processing new post: {e}")
    
    async def _send_emoji_comment(
        self,
        channel: str,
        post_id: int,
        emoji: str
    ) -> Optional[Dict]:
        """Send emoji as first comment."""
        try:
            # Get discussion message (the one in comments group)
            full_message = await self.client.client.get_messages(
                channel,
                ids=post_id
            )
            
            if not full_message or not full_message.replies:
                logger.warning(f"🎯 No discussion group for @{channel}:{post_id}")
                return None
            
            # Get discussion group
            discussion_msg = await full_message.get_reply_message()
            if not discussion_msg:
                logger.warning(f"🎯 Cannot get discussion for @{channel}:{post_id}")
                return None
            
            discussion_chat = await discussion_msg.get_chat()
            
            # Send emoji as reply
            sent = await self.client.client.send_message(
                discussion_chat,
                emoji,
                reply_to=discussion_msg.id
            )
            
            return {
                "message_id": sent.id,
                "chat_id": discussion_chat.id,
                "emoji": emoji
            }
            
        except Exception as e:
            logger.error(f"❌ Emoji send error: {e}")
            return None
    
    async def _edit_worker(self) -> None:
        """Background worker that processes edit queue."""
        logger.info("📝 Edit worker started")
        
        while self._monitoring:
            try:
                # Wait for next pending edit
                pending = await asyncio.wait_for(
                    self.pending_edits.get(),
                    timeout=5.0
                )
                
                # Wait for edit delay
                wait_seconds = pending.edit_after
                logger.info(f"⏳ [EDIT] Waiting {wait_seconds}s before editing {pending.emoji_msg_id}")
                
                while wait_seconds > 0 and self._monitoring:
                    await asyncio.sleep(min(10, wait_seconds))
                    wait_seconds -= 10
                
                if not self._monitoring:
                    break
                
                # Generate promo text
                promo_text = await self.promo_engine.generate_promo_comment(
                    post_text=pending.post_text,
                    target_link=pending.target_link
                )
                
                # Edit the emoji comment to promo
                success = await self._edit_to_promo(pending, promo_text)
                
                if success:
                    self.stats["edits_completed"] += 1
                    logger.info(f"✅ [EDIT] Completed: @{pending.channel}:{pending.post_id}")
                    
                    if self.on_edit_complete:
                        await self.on_edit_complete(pending, promo_text)
                else:
                    self.stats["edits_failed"] += 1
                    logger.warning(f"❌ [EDIT] Failed: @{pending.channel}:{pending.post_id}")
                
                self.pending_edits.task_done()
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Edit worker error: {e}")
    
    async def _edit_to_promo(
        self,
        pending: PendingEdit,
        new_text: str
    ) -> bool:
        """Edit emoji comment to promo text."""
        try:
            # Get the discussion chat
            full_message = await self.client.client.get_messages(
                pending.channel,
                ids=pending.post_id
            )
            
            if not full_message:
                return False
            
            discussion_msg = await full_message.get_reply_message()
            if not discussion_msg:
                return False
            
            discussion_chat = await discussion_msg.get_chat()
            
            # Edit the message
            await self.client.client.edit_message(
                discussion_chat,
                pending.emoji_msg_id,
                new_text
            )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Edit error: {e}")
            return False
    
    def _get_random_emoji(self) -> str:
        """Get random emoji from pool."""
        import random
        return random.choice(self.EMOJI_COMMENTS)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current sniper status."""
        return {
            "monitoring": self._monitoring,
            "pending_edits": self.pending_edits.qsize(),
            "posts_seen": self.stats["posts_seen"],
            "emoji_sent": self.stats["emoji_sent"],
            "edits_completed": self.stats["edits_completed"],
            "edits_failed": self.stats["edits_failed"],
            "monitored_channels": len(self._handlers)
        }
    
    def get_formatted_status(self) -> str:
        """Get human-readable status."""
        status = self.get_status()
        emoji = "🟢" if status["monitoring"] else "🔴"
        
        return f"""
{emoji} <b>Comment Sniper Status</b>

<b>State:</b> {"Active" if status["monitoring"] else "Stopped"}
<b>Channels:</b> {status["monitored_channels"]}
<b>Pending edits:</b> {status["pending_edits"]}

<b>Stats:</b>
• Posts seen: {status["posts_seen"]}
• Emoji sent: {status["emoji_sent"]}
• Edits completed: {status["edits_completed"]}
• Edits failed: {status["edits_failed"]}
"""


# Need random import at top
import random
