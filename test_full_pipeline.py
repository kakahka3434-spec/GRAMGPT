"""
Full pipeline test: Parse + Generate Comment + Send
Tests the complete workflow:
1. Parse last messages from channel
2. Generate AI comment based on message content
3. Send comment (optional - asks first)
"""

import asyncio
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

from src.services.telegram_user_client import TelegramUserClient
from src.core.ai_client import ai_client
from src.config import settings


async def generate_comment(text: str, context: str = "") -> str:
    """Generate a natural comment based on post content."""
    prompt = f"""Прочитай этот пост из Telegram канала и напиши короткий естественный комментарий (1-2 предложения), как будто от обычного пользователя:

Пост:
{text[:500]}

Напиши только текст комментария, без пояснений:"""
    
    messages = [{"role": "user", "content": prompt}]
    response = await ai_client.get_chat_response(0, messages)
    
    # Clean up response
    comment = response.strip().strip('"')
    return comment


async def test_pipeline():
    """Test full parse + AI comment + send pipeline."""
    
    print("=" * 60)
    print("🚀 Full Pipeline Test: Parse → AI → Comment")
    print("=" * 60)
    
    TARGET_CHANNEL = "durov"
    
    # Check config
    if not settings.telegram_api_id:
        print("❌ Telegram API not configured")
        return False
    
    if not ai_client.client:
        print("⚠️  AI client not initialized - comments won't be generated")
    
    # Connect
    client = TelegramUserClient(
        api_id=settings.telegram_api_id,
        api_hash=settings.telegram_api_hash,
        phone=settings.telegram_phone,
        session_path="data/sessions/gramgpt_user"
    )
    
    connected = await client.connect()
    if not connected:
        print("❌ Connection failed")
        return False
    
    me = await client.get_me()
    print(f"\n👤 Logged in as: @{me['username']}")
    
    # Parse messages
    print(f"\n📨 Parsing last 3 messages from @{TARGET_CHANNEL}...")
    messages = await client.parse_last_messages(TARGET_CHANNEL, limit=3)
    
    if not messages:
        print("❌ No messages found")
        await client.disconnect()
        return False
    
    print(f"✅ Found {len(messages)} messages")
    
    # For each message, generate and optionally send comment
    for msg in messages[:2]:  # Test on first 2 messages
        print(f"\n{'='*60}")
        print(f"📄 Message ID {msg['id']} | {msg['date'][:10] if msg['date'] else 'N/A'}")
        print(f"   Views: {msg['views']} | Comments: {msg['comments_count']}")
        text_preview = msg['text'][:150].replace('\n', ' ') if msg['text'] else "(no text)"
        if len(msg['text'] or "") > 150:
            text_preview += "..."
        print(f"   Text: {text_preview}")
        
        # Generate AI comment
        if ai_client.client:
            print(f"\n🤖 Generating AI comment...")
            comment = await generate_comment(msg['text'])
            print(f"   Generated: \"{comment}\"")
            
            # Ask if user wants to send
            confirm = input(f"\n   Send this comment? (yes/no/skip): ").strip().lower()
            
            if confirm in ("yes", "y"):
                result = await client.send_comment(
                    channel=TARGET_CHANNEL,
                    message_id=msg['id'],
                    text=comment
                )
                if result:
                    print(f"   ✅ Comment sent! ID: {result['id']}")
                else:
                    print(f"   ❌ Failed to send")
            else:
                print(f"   ⏭️  Skipped")
        else:
            print(f"\n⚠️  AI not available - skipping comment generation")
    
    await client.disconnect()
    
    print(f"\n{'='*60}")
    print("✅ Pipeline test complete!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_pipeline())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted")
        sys.exit(1)
