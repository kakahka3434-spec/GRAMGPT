"""
Test script for TelegramUserClient.
Run this to verify the client works correctly.
"""

import asyncio
import logging
import sys

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

from src.services.telegram_user_client import TelegramUserClient
from src.config import settings


async def test_client():
    """Test the TelegramUserClient implementation."""
    
    # Check if credentials are configured
    if not settings.telegram_api_id or not settings.telegram_api_hash:
        print("\n❌ ERROR: Telegram API credentials not configured!")
        print("\nPlease add to your .env file:")
        print("TELEGRAM_API_ID=your_api_id_here")
        print("TELEGRAM_API_HASH=your_api_hash_here")
        print("TELEGRAM_PHONE=your_phone_number_here (e.g., +79123456789)")
        print("\nGet API credentials from https://my.telegram.org")
        return False
    
    if not settings.telegram_phone:
        print("\n❌ ERROR: Phone number not configured!")
        print("Add TELEGRAM_PHONE=+79123456789 to your .env file")
        return False
    
    print(f"\n🔧 Testing TelegramUserClient with phone: {settings.telegram_phone}")
    print("=" * 60)
    
    client = TelegramUserClient(
        api_id=settings.telegram_api_id,
        api_hash=settings.telegram_api_hash,
        phone=settings.telegram_phone,
        session_path="data/sessions/gramgpt_user"
    )
    
    # Test connection
    connected = await client.connect()
    if not connected:
        print("\n❌ FAILED: Could not connect to Telegram")
        return False
    
    print("\n✅ Connected successfully!")
    
    # Test get_me
    user_info = await client.get_me()
    if not user_info:
        print("❌ FAILED: Could not get user info")
        await client.disconnect()
        return False
    
    print(f"\n👤 Account Info:")
    print(f"   ID: {user_info['id']}")
    print(f"   Username: @{user_info['username']}" if user_info['username'] else "   Username: (none)")
    print(f"   Name: {user_info['first_name']} {user_info.get('last_name', '')}".strip())
    print(f"   Phone: {user_info['phone']}")
    
    # Test message parsing
    print("\n📨 Testing message parsing from @durov...")
    messages = await client.parse_last_messages("durov", limit=5)
    
    if not messages:
        print("⚠️  WARNING: Could not fetch messages from @durov (might be restricted or empty)")
    else:
        print(f"\n✅ Fetched {len(messages)} messages:")
        for i, msg in enumerate(messages[:3], 1):
            text_preview = msg['text'][:100].replace('\n', ' ') if msg['text'] else "(no text)"
            if len(msg['text'] or "") > 100:
                text_preview += "..."
            print(f"\n   {i}. ID: {msg['id']} | Date: {msg['date'][:10] if msg['date'] else 'N/A'}")
            print(f"      Views: {msg['views']} | Comments: {msg['comments_count']}")
            print(f"      Text: {text_preview}")
    
    # Disconnect
    await client.disconnect()
    
    print("\n" + "=" * 60)
    print("✅ All tests passed! Client is working correctly.")
    print("=" * 60)
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_client())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Unexpected error: {e}")
        sys.exit(1)
