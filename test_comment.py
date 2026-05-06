"""
Test script for sending comments via TelegramUserClient.
⚠️  WARNING: This will actually post a comment to the specified channel!
"""

import asyncio
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

from src.services.telegram_user_client import TelegramUserClient
from src.config import settings


async def test_comment():
    """Test sending a comment to a channel post."""
    
    # Check configuration
    if not settings.telegram_api_id:
        print("❌ Telegram API not configured!")
        return False
    
    # Test settings
    TEST_CHANNEL = "durov"  # Channel to comment on
    TEST_MESSAGE_ID = 501  # Message ID from earlier test
    TEST_COMMENT = "👍 Interesting post! Thanks for sharing."
    
    print("=" * 60)
    print("📝 Testing Comment Feature")
    print("=" * 60)
    print(f"\n⚠️  This will post a REAL comment to @{TEST_CHANNEL}")
    print(f"   Message ID: {TEST_MESSAGE_ID}")
    print(f"   Comment: {TEST_COMMENT}")
    
    confirm = input("\n   Continue? (yes/no): ").strip().lower()
    if confirm not in ("yes", "y"):
        print("\n❌ Aborted by user")
        return False
    
    client = TelegramUserClient(
        api_id=settings.telegram_api_id,
        api_hash=settings.telegram_api_hash,
        phone=settings.telegram_phone,
        session_path="data/sessions/gramgpt_user"
    )
    
    # Connect (uses saved session)
    connected = await client.connect()
    if not connected:
        print("❌ Failed to connect")
        return False
    
    # Show account info
    me = await client.get_me()
    if me:
        print(f"\n👤 Commenting as: @{me['username']}")
    
    # Send comment
    print(f"\n📨 Sending comment...")
    result = await client.send_comment(
        channel=TEST_CHANNEL,
        message_id=TEST_MESSAGE_ID,
        text=TEST_COMMENT
    )
    
    if result:
        print(f"\n✅ Comment sent successfully!")
        print(f"   Comment ID: {result['id']}")
        print(f"   View: https://t.me/{TEST_CHANNEL}/{TEST_MESSAGE_ID}")
    else:
        print(f"\n❌ Failed to send comment")
        print(f"   Possible reasons:")
        print(f"   - Channel has no discussion group enabled")
        print(f"   - Flood wait (too many comments)")
        print(f"   - Message ID doesn't exist")
    
    # Disconnect
    await client.disconnect()
    
    return result is not None


if __name__ == "__main__":
    try:
        success = asyncio.run(test_comment())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted")
        sys.exit(1)
