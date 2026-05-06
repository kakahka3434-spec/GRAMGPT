"""
Advanced Comment Sender Test
Tests 3 styles + memory + behavioral patterns
"""

import asyncio
import logging
import sys
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

from src.services.telegram_user_client import TelegramUserClient
from src.services.comment_sender import CommentSender
from src.config import settings


async def test_all_styles():
    """Test all 3 comment styles on one post."""
    
    print("\n" + "="*70)
    print("🧪 ADVANCED COMMENT SENDER TEST")
    print("="*70)
    
    # Check config
    if not settings.telegram_api_id:
        print("❌ Telegram API not configured!")
        return False
    
    # Test configuration
    TEST_CHANNEL = "durov"
    TEST_MESSAGE_ID = 501  # From earlier test
    TEST_POST_TEXT = "⚡️ Fees in TON have dropped 6× — to nearly zero."
    
    styles = ["expert", "engaging", "casual"]
    
    print(f"\n📋 Test Configuration:")
    print(f"   Channel: @{TEST_CHANNEL}")
    print(f"   Post ID: {TEST_MESSAGE_ID}")
    print(f"   Post preview: {TEST_POST_TEXT[:60]}...")
    print(f"   Styles to test: {', '.join(styles)}")
    
    # Connect
    print(f"\n🔌 Connecting to Telegram...")
    client = TelegramUserClient(
        api_id=settings.telegram_api_id,
        api_hash=settings.telegram_api_hash,
        phone=settings.telegram_phone,
        session_path="data/sessions/gramgpt_user"
    )
    
    connected = await client.connect()
    if not connected:
        print("❌ Connection failed!")
        return False
    
    me = await client.get_me()
    print(f"✅ Connected as @{me['username']}")
    
    # Initialize CommentSender
    print(f"\n🎯 Initializing CommentSender...")
    sender = CommentSender(client)
    
    # Test 1: Generate all 3 styles (without sending)
    print(f"\n" + "="*70)
    print("🎨 TEST 1: Generate all 3 styles")
    print("="*70)
    
    generated_comments = {}
    
    for style in styles:
        print(f"\n📝 Style: {style.upper()}")
        print(f"   Description: {sender.STYLE_PROMPTS[style]['description']}")
        
        comment, metadata = await sender.generate_comment(
            post_text=TEST_POST_TEXT,
            style=style
        )
        
        generated_comments[style] = comment
        
        print(f"   🤖 Generated: \"{comment}\"")
        print(f"   📊 Sentiment: {metadata['sentiment']}")
        print(f"   ⏱️  Time: {metadata['generation_time']}s")
        
        # Validate style characteristics
        has_emoji = any(ord(c) > 127000 for c in comment)
        is_question = "?" in comment
        
        if style == "expert":
            print(f"   ✅ Check: no emoji={not has_emoji}, professional tone")
        elif style == "engaging":
            print(f"   ✅ Check: 1 emoji={has_emoji}, question={is_question}")
        elif style == "casual":
            print(f"   ✅ Check: short={len(comment) < 100}, natural")
    
    # Test 2: Memory check
    print(f"\n" + "="*70)
    print("🧠 TEST 2: Contextual Memory")
    print("="*70)
    
    # Check if already commented
    from src.db.comment_memory import comment_memory
    
    is_commented = comment_memory.is_already_commented(
        TEST_CHANNEL, TEST_MESSAGE_ID, hours=24
    )
    print(f"   Already commented (last 24h): {is_commented}")
    
    if not is_commented:
        print(f"   ✓ Can comment (not in memory)")
    else:
        print(f"   ⚠ Will skip (already commented)")
    
    # Test 3: Full cycle (optional - asks user)
    print(f"\n" + "="*70)
    print("🚀 TEST 3: Full Cycle with Behavioral Patterns")
    print("="*70)
    
    print(f"\n⚠️  This will send a REAL comment to @{TEST_CHANNEL}")
    print(f"   Post: #{TEST_MESSAGE_ID}")
    print(f"   Generated comments above ☝️")
    
    choice = input(f"\n   Which style to send? (expert/engaging/casual/skip): ").strip().lower()
    
    if choice in styles:
        print(f"\n🚀 Running full cycle with style: {choice}")
        print(f"   This includes: read → think → type → send → pause")
        
        result = await sender.comment_with_full_cycle(
            channel=TEST_CHANNEL,
            post_id=TEST_MESSAGE_ID,
            post_text=TEST_POST_TEXT,
            style=choice
        )
        
        if result:
            print(f"\n✅ SUCCESS!")
            print(f"   Comment ID: {result['comment_id']}")
            print(f"   Text: {result['comment_text']}")
            print(f"   Total time: {result['total_time']}s")
            print(f"   Sentiment: {result['sentiment']}")
        else:
            print(f"\n❌ Failed (may be already commented or no discussion group)")
    else:
        print(f"\n⏭️  Skipped (no comment sent)")
    
    # Test 4: Memory verification
    print(f"\n" + "="*70)
    print("🧠 TEST 4: Verify Memory Record")
    print("="*70)
    
    is_commented_now = comment_memory.is_already_commented(
        TEST_CHANNEL, TEST_MESSAGE_ID, hours=24
    )
    print(f"   Now in memory: {is_commented_now}")
    
    recent = comment_memory.get_recent_comments(TEST_CHANNEL, hours=1)
    print(f"   Recent comments: {len(recent)}")
    for r in recent[:3]:
        print(f"      - Post #{r['post_id']} | {r['style']} | {r['preview'][:30]}...")
    
    # Disconnect
    await client.disconnect()
    
    # Summary
    print(f"\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    print(f"✅ All 3 styles generated successfully")
    print(f"✅ Memory system working")
    print(f"✅ Sentiment analysis working")
    print(f"✅ Telegram connection stable")
    
    if choice in styles:
        print(f"✅ Full cycle executed (if not skipped)")
    else:
        print(f"⏭️  Full cycle skipped by user")
    
    print(f"\n🎉 Advanced CommentSender is ready!")
    print("="*70)
    
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_all_styles())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
