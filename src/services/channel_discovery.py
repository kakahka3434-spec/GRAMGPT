"""
Channel Discovery - Auto-search and filter channels with open comments.
Searches by keywords and validates comment availability.
"""

import asyncio
import logging
import sqlite3
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any

from telethon.tl.functions.contacts import SearchRequest
from telethon.tl.types import Channel, Chat, ChatForbidden, ChannelForbidden

logger = logging.getLogger(__name__)


class ChannelDiscovery:
    """
    Discovers Telegram channels by keywords and filters for open comments.
    """
    
    def __init__(self, telegram_client, cache_db: str = "data/channel_cache.db"):
        """
        Initialize channel discovery.
        
        Args:
            telegram_client: Connected TelegramUserClient
            cache_db: SQLite cache for channel metadata
        """
        self.client = telegram_client
        self.cache_db = cache_db
        self._ensure_cache_db()
        
        logger.info("🔍 ChannelDiscovery initialized")
    
    def _ensure_cache_db(self) -> None:
        """Create cache database for channel metadata."""
        os.makedirs(os.path.dirname(self.cache_db), exist_ok=True)
        
        with sqlite3.connect(self.cache_db) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS channel_cache (
                    username TEXT PRIMARY KEY,
                    title TEXT,
                    members INTEGER,
                    has_comments INTEGER,
                    last_post_date TEXT,
                    is_restricted INTEGER,
                    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
    
    async def search_by_keywords(
        self,
        keywords: List[str],
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search for channels by keywords.
        
        Args:
            keywords: List of search terms (e.g., ['crypto', 'trading', 'nft'])
            limit: Max results per keyword
        
        Returns:
            List of channel dicts with metadata
        """
        results = []
        seen_usernames = set()
        
        for keyword in keywords:
            logger.info(f"🔍 Searching for: '{keyword}'")
            
            try:
                # Use Telegram global search
                search_result = await self.client.client(
                    SearchRequest(
                        q=keyword,
                        limit=limit
                    )
                )
                
                for chat in search_result.chats:
                    if isinstance(chat, (Channel, Chat)):
                        username = getattr(chat, 'username', None)
                        if not username:
                            continue
                        
                        # Skip if already seen
                        if username in seen_usernames:
                            continue
                        seen_usernames.add(username)
                        
                        # Extract metadata
                        channel_data = {
                            "username": username,
                            "title": getattr(chat, 'title', 'Unknown'),
                            "members": getattr(chat, 'participants_count', 0),
                            "has_comments": False,  # Will check separately
                            "is_broadcast": getattr(chat, 'broadcast', False),
                            "is_restricted": False,
                            "last_post_date": None
                        }
                        
                        results.append(channel_data)
                        
            except Exception as e:
                logger.error(f"❌ Search error for '{keyword}': {e}")
                continue
            
            # Rate limit between keywords
            await asyncio.sleep(2)
        
        logger.info(f"🔍 Found {len(results)} unique channels")
        return results
    
    async def filter_open_comments(
        self,
        channels: List[Dict[str, Any]],
        skip_cache: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Filter channels that have open comments enabled.
        
        Args:
            channels: List of channel dicts from search
            skip_cache: If True, bypass cache and re-check
        
        Returns:
            Channels with has_comments=True
        """
        valid_channels = []
        
        for channel in channels:
            username = channel["username"]
            
            # Check cache first
            if not skip_cache:
                cached = self._get_cached_channel(username)
                if cached and cached.get("checked_at"):
                    checked_time = datetime.fromisoformat(cached["checked_at"])
                    if datetime.now() - checked_time < timedelta(days=7):
                        # Use cached result if < 7 days old
                        if cached.get("has_comments"):
                            channel.update(cached)
                            valid_channels.append(channel)
                            logger.debug(f"📦 Cache hit: @{username} (has comments)")
                        continue
            
            # Live check
            try:
                entity = await self.client.client.get_entity(username)
                
                if isinstance(entity, Channel):
                    # Check if channel has linked discussion group
                    has_discussion = bool(getattr(entity, 'has_link', False))
                    
                    # Check if not restricted
                    is_restricted = bool(
                        getattr(entity, 'restricted', False) or
                        getattr(entity, 'forbidden', False)
                    )
                    
                    # Update channel data
                    channel["has_comments"] = has_discussion
                    channel["is_restricted"] = is_restricted
                    channel["members"] = getattr(entity, 'participants_count', channel.get("members", 0))
                    
                    # Cache result
                    self._cache_channel(channel)
                    
                    if has_discussion and not is_restricted:
                        valid_channels.append(channel)
                        logger.info(f"✅ @{username}: Open comments, {channel['members']} members")
                    else:
                        logger.debug(f"❌ @{username}: No comments or restricted")
                
                # Rate limit
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.warning(f"⚠️ Could not check @{username}: {e}")
                continue
        
        logger.info(f"✅ Found {len(valid_channels)}/{len(channels)} channels with open comments")
        return valid_channels
    
    def _get_cached_channel(self, username: str) -> Optional[Dict]:
        """Get cached channel data."""
        try:
            with sqlite3.connect(self.cache_db) as conn:
                cursor = conn.execute(
                    "SELECT * FROM channel_cache WHERE username = ?",
                    (username,)
                )
                row = cursor.fetchone()
                if row:
                    return {
                        "username": row[0],
                        "title": row[1],
                        "members": row[2],
                        "has_comments": bool(row[3]),
                        "last_post_date": row[4],
                        "is_restricted": bool(row[5]),
                        "checked_at": row[6]
                    }
        except Exception as e:
            logger.error(f"Cache read error: {e}")
        return None
    
    def _cache_channel(self, channel: Dict) -> None:
        """Cache channel metadata."""
        try:
            with sqlite3.connect(self.cache_db) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO channel_cache 
                    (username, title, members, has_comments, last_post_date, is_restricted, checked_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        channel["username"],
                        channel["title"],
                        channel["members"],
                        int(channel.get("has_comments", False)),
                        channel.get("last_post_date"),
                        int(channel.get("is_restricted", False)),
                        datetime.now().isoformat()
                    )
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Cache write error: {e}")
    
    async def discover_target_channels(
        self,
        keywords: List[str],
        min_members: int = 1000,
        max_results: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Full discovery pipeline: search → filter → quality check.
        
        Args:
            keywords: Search terms
            min_members: Minimum subscriber count
            max_results: Max channels to return
        
        Returns:
            High-quality target channels with open comments
        """
        logger.info(f"🎯 Starting discovery: keywords={keywords}, min_members={min_members}")
        
        # 1. Search
        all_channels = await self.search_by_keywords(keywords, limit=50)
        
        # 2. Quick filter by members
        popular = [c for c in all_channels if c.get("members", 0) >= min_members]
        logger.info(f"📊 Filtered to {len(popular)} channels with {min_members}+ members")
        
        # 3. Check for open comments
        with_comments = await self.filter_open_comments(popular[:max_results * 2])
        
        # 4. Return top results
        result = with_comments[:max_results]
        
        logger.info(f"🎯 Discovery complete: {len(result)} high-quality targets")
        return result
