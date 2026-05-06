"""
Comment Memory Module - tracks commented posts to avoid duplicates.
Simple SQLite implementation for GRAMGPT.
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


class CommentMemory:
    """
    Tracks which posts have been commented on to avoid duplicates.
    """
    
    def __init__(self, db_path: str = "gramgpt.db"):
        self.db_path = db_path
        self._init_table()
    
    def _init_table(self):
        """Create commented_posts table if not exists."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS commented_posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel TEXT NOT NULL,
                    post_id INTEGER NOT NULL,
                    timestamp REAL NOT NULL,
                    style TEXT,
                    comment_preview TEXT,
                    UNIQUE(channel, post_id)
                )
            """)
            # Index for fast lookups
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_commented_posts_lookup 
                ON commented_posts(channel, post_id, timestamp)
            """)
            conn.commit()
            logger.debug("🧠 [memory] Таблица commented_posts готова")
    
    def is_already_commented(self, channel: str, post_id: int, hours: int = 24) -> bool:
        """
        Check if a post was commented within the last N hours.
        
        Args:
            channel: Channel username
            post_id: Post/message ID
            hours: Time window to check (default: 24 hours)
        
        Returns:
            True if already commented, False otherwise
        """
        cutoff_time = (datetime.now() - timedelta(hours=hours)).timestamp()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT 1 FROM commented_posts 
                WHERE channel = ? AND post_id = ? AND timestamp > ?
                LIMIT 1
                """,
                (channel, post_id, cutoff_time)
            )
            result = cursor.fetchone()
            
            is_commented = result is not None
            if is_commented:
                logger.debug(f"🧠 [memory] Найдено: @{channel} #{post_id} (за последние {hours}ч)")
            
            return is_commented
    
    def record_comment(
        self, 
        channel: str, 
        post_id: int, 
        style: str = "unknown",
        comment_preview: str = ""
    ) -> bool:
        """
        Record that a comment was sent to a post.
        
        Args:
            channel: Channel username
            post_id: Post/message ID
            style: Comment style used
            comment_preview: First 100 chars of comment text
        
        Returns:
            True if recorded successfully
        """
        try:
            timestamp = datetime.now().timestamp()
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO commented_posts 
                    (channel, post_id, timestamp, style, comment_preview)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (channel, post_id, timestamp, style, comment_preview[:100])
                )
                conn.commit()
            
            logger.info(f"🧠 [memory] Записано: @{channel} #{post_id} | style: {style}")
            return True
            
        except Exception as e:
            logger.error(f"❌ [memory] Ошибка записи: {e}")
            return False
    
    def get_recent_comments(self, channel: str, hours: int = 24) -> list:
        """
        Get list of recently commented posts for a channel.
        
        Args:
            channel: Channel username
            hours: Time window
        
        Returns:
            List of dicts with post info
        """
        cutoff_time = (datetime.now() - timedelta(hours=hours)).timestamp()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT post_id, timestamp, style, comment_preview 
                FROM commented_posts 
                WHERE channel = ? AND timestamp > ?
                ORDER BY timestamp DESC
                """,
                (channel, cutoff_time)
            )
            
            results = []
            for row in cursor.fetchall():
                post_id, ts, style, preview = row
                results.append({
                    "post_id": post_id,
                    "datetime": datetime.fromtimestamp(ts).isoformat(),
                    "style": style,
                    "preview": preview
                })
            
            return results
    
    def clear_old_records(self, days: int = 30) -> int:
        """
        Clear records older than N days.
        
        Args:
            days: Age threshold for deletion
        
        Returns:
            Number of records deleted
        """
        cutoff_time = (datetime.now() - timedelta(days=days)).timestamp()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM commented_posts WHERE timestamp < ?",
                (cutoff_time,)
            )
            conn.commit()
            deleted = cursor.rowcount
        
        logger.info(f"🧹 [memory] Очищено {deleted} старых записей (> {days} дней)")
        return deleted
    
    def get_all_recent(self, hours: int = 24) -> list:
        """
        Get all recent comments across all channels.
        
        Args:
            hours: Time window
        
        Returns:
            List of all comment records
        """
        cutoff_time = (datetime.now() - timedelta(hours=hours)).timestamp()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT channel, post_id, timestamp, style, comment_preview 
                FROM commented_posts 
                WHERE timestamp > ?
                ORDER BY timestamp DESC
                """,
                (cutoff_time,)
            )
            
            results = []
            for row in cursor.fetchall():
                channel, post_id, ts, style, preview = row
                results.append({
                    "channel": channel,
                    "post_id": post_id,
                    "datetime": datetime.fromtimestamp(ts).isoformat(),
                    "timestamp": ts,
                    "style": style,
                    "comment_preview": preview
                })
            
            return results


# Global instance
comment_memory = CommentMemory()
