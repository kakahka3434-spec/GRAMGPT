"""
Telegram User Client - Telethon wrapper for GRAMGPT.
Handles user API connection, session management, and message parsing.
"""

import logging
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

from telethon import TelegramClient
from telethon.errors import (
    FloodWaitError,
    PhoneNumberInvalidError,
    AuthKeyUnregisteredError,
)
from telethon.tl.functions.messages import GetMessagesViewsRequest
from telethon.tl.types import PeerChannel

# Configure logger
logger = logging.getLogger(__name__)


class TelegramUserClient:
    """
    Async Telegram User API client using Telethon.
    
    Handles:
    - Connection with session persistence
    - Authorization flow (phone code)
    - Message parsing from channels
    - Basic error handling for common Telegram errors
    """
    
    def __init__(
        self,
        api_id: int,
        api_hash: str,
        phone: str,
        session_path: str = "data/sessions/gramgpt_user"
    ):
        """
        Initialize the Telegram User Client.
        
        Args:
            api_id: Telegram API ID from my.telegram.org
            api_hash: Telegram API Hash from my.telegram.org
            phone: Phone number with country code (e.g., +79123456789)
            session_path: Path to store session file
        """
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone = phone
        self.session_path = session_path
        
        # Ensure session directory exists
        session_dir = os.path.dirname(session_path)
        if session_dir and not os.path.exists(session_dir):
            os.makedirs(session_dir, exist_ok=True)
        
        # Initialize client (not started yet)
        self._client: Optional[TelegramClient] = None
        self._is_connected = False
        
        logger.info(f"TelegramUserClient initialized for phone: {phone}")
    
    async def connect(self) -> bool:
        """
        Connect to Telegram and authorize if needed.
        
        On first run: prompts for verification code via console.
        On subsequent runs: uses saved session.
        
        Returns:
            bool: True if connected and authorized successfully
        """
        try:
            if self._client is None:
                self._client = TelegramClient(
                    self.session_path,
                    self.api_id,
                    self.api_hash
                )
            
            logger.info("Connecting to Telegram...")
            await self._client.connect()
            
            if not await self._client.is_user_authorized():
                logger.info(f"Authorization required for {self.phone}")
                logger.info("Requesting verification code...")
                
                await self._client.send_code_request(self.phone)
                
                # Get code from console input
                code = input(f"Enter the verification code sent to {self.phone}: ")
                
                try:
                    await self._client.sign_in(self.phone, code)
                    logger.info("Successfully authorized!")
                except Exception as e:
                    logger.error(f"Failed to sign in: {e}")
                    return False
            else:
                logger.info("Using existing session, already authorized")
            
            self._is_connected = True
            logger.info("Connected to Telegram successfully")
            return True
            
        except FloodWaitError as e:
            logger.error(f"Flood wait error: wait {e.seconds} seconds before retrying")
            return False
        except PhoneNumberInvalidError:
            logger.error(f"Invalid phone number: {self.phone}")
            return False
        except AuthKeyUnregisteredError:
            logger.error("Session expired or invalid, will need re-authorization")
            # Remove session file to force re-auth
            session_file = f"{self.session_path}.session"
            if os.path.exists(session_file):
                os.remove(session_file)
                logger.info(f"Removed invalid session file: {session_file}")
            return False
        except ConnectionError as e:
            logger.error(f"Connection error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during connection: {e}")
            return False
    
    async def get_me(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the current user.
        
        Returns:
            Dict with keys: id, username, first_name, last_name, phone
            None if not connected
        """
        if not self._is_connected or self._client is None:
            logger.error("Not connected. Call connect() first.")
            return None
        
        try:
            me = await self._client.get_me()
            if me:
                user_info = {
                    "id": me.id,
                    "username": me.username or "",
                    "first_name": me.first_name or "",
                    "last_name": me.last_name or "",
                    "phone": me.phone or "",
                }
                logger.info(
                    f"Account info: ID={me.id}, "
                    f"Username=@{me.username or 'N/A'}, "
                    f"Name={me.first_name or 'N/A'}"
                )
                return user_info
            return None
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return None
    
    async def parse_last_messages(
        self,
        channel: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Parse last messages from a channel.
        
        Args:
            channel: Channel username (with or without @) or invite link
            limit: Number of messages to fetch (default: 5)
        
        Returns:
            List of message dicts with keys:
                - id: message ID
                - text: message text content
                - date: ISO format datetime string
                - views: view count (if available)
                - comments_count: replies count (if available)
        """
        if not self._is_connected or self._client is None:
            logger.error("Not connected. Call connect() first.")
            return []
        
        # Normalize channel username
        channel = channel.strip()
        if channel.startswith("https://t.me/"):
            channel = channel.split("/")[-1].split("?")[0]
        if channel.startswith("@"):
            channel = channel[1:]
        
        messages = []
        
        try:
            logger.info(f"Fetching last {limit} messages from @{channel}...")
            
            # Get the channel entity
            entity = await self._client.get_entity(channel)
            
            # Iterate messages
            async for message in self._client.iter_messages(entity, limit=limit):
                msg_data = {
                    "id": message.id,
                    "text": message.text or "",
                    "date": message.date.isoformat() if message.date else None,
                    "views": message.views if message.views else 0,
                    "comments_count": 0,  # Will be updated below if available
                }
                
                # Try to get replies count if available
                if hasattr(message, 'replies') and message.replies:
                    msg_data["comments_count"] = message.replies.replies or 0
                
                messages.append(msg_data)
            
            logger.info(f"Successfully fetched {len(messages)} messages from @{channel}")
            
        except FloodWaitError as e:
            logger.error(f"Flood wait: need to wait {e.seconds} seconds")
        except Exception as e:
            logger.error(f"Error parsing messages from @{channel}: {e}")
        
        return messages
    
    async def send_comment(
        self,
        channel: str,
        message_id: int,
        text: str,
        reply_to_comment: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Send a comment to a channel post.
        
        Note: Comments work only if the channel has a linked discussion group.
        
        Args:
            channel: Channel username (with or without @)
            message_id: ID of the channel post to comment on
            text: Comment text
            reply_to_comment: Optional comment ID to reply to
        
        Returns:
            Dict with comment info on success: id, text, date
            None on failure
        """
        if not self._is_connected or self._client is None:
            logger.error("Not connected. Call connect() first.")
            return None
        
        # Normalize channel username
        channel = channel.strip()
        if channel.startswith("https://t.me/"):
            channel = channel.split("/")[-1].split("?")[0]
        if channel.startswith("@"):
            channel = channel[1:]
        
        try:
            logger.info(f"Sending comment to @{channel} post {message_id}...")
            
            # Get channel entity
            entity = await self._client.get_entity(channel)
            
            # Get the full channel info to check for linked chat
            from telethon.tl.functions.channels import GetFullChannelRequest
            full_channel = await self._client(GetFullChannelRequest(channel=entity))
            
            # Get the discussion group (linked chat) if exists
            linked_chat_id = full_channel.full_chat.linked_chat_id
            if not linked_chat_id:
                logger.error(f"Channel @{channel} has no discussion group enabled")
                return None
            
            # Get the discussion group entity
            discussion_group = await self._client.get_entity(linked_chat_id)
            
            # Send message to discussion group with reply_to=message_id
            # This creates a comment on the original channel post
            comment = await self._client.send_message(
                entity=discussion_group,
                message=text,
                reply_to=message_id
            )
            
            if comment:
                result = {
                    "id": comment.id,
                    "text": comment.text or "",
                    "date": comment.date.isoformat() if comment.date else None,
                    "channel": channel,
                    "message_id": message_id,
                }
                logger.info(f"Comment sent successfully! ID: {comment.id}")
                return result
            
            return None
            
        except FloodWaitError as e:
            logger.error(f"Flood wait: need to wait {e.seconds} seconds before commenting")
            return None
        except Exception as e:
            logger.error(f"Error sending comment to @{channel}: {e}")
            return None
    
    async def disconnect(self) -> None:
        """
        Disconnect from Telegram and clean up.
        Safe to call even if not connected.
        """
        if self._client is not None:
            try:
                logger.info("Disconnecting from Telegram...")
                await self._client.disconnect()
                logger.info("Disconnected successfully")
            except Exception as e:
                logger.warning(f"Error during disconnect: {e}")
            finally:
                self._is_connected = False
                self._client = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
