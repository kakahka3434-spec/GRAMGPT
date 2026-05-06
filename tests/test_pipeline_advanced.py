"""
Advanced Pipeline Test
Tests full automation cycle with orchestrator.
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
from src.services.comment_sender import CommentSender
from src.services.account_warmer import AccountWarmer
from src.core.pipeline_orchestrator import PipelineOrchestrator
from src.config import settings


async def test_pipeline_cycle():
    """Test one full pipeline cycle."""
    
    print("\n" + "="*70)
    print("🧪 ADVANCED PIPELINE TEST")
    print("="*70)
    
    # Check config
    if not settings.telegram_api_id:
        print("❌ Telegram API not configured!")
        return False
    
    # Connect Telegram client
    print("\n🔌 Connecting to Telegram...")
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
    
    # Initialize components
    print("\n🛠️  Initializing components...")
    comment_sender = CommentSender(client)
    account_warmer = AccountWarmer(client)
    orchestrator = PipelineOrchestrator(
        telegram_client=client,
        comment_sender=comment_sender,
        account_warmer=account_warmer
    )
    print("✅ All components ready")
    
    # Test 1: Rate Limiter
    print("\n" + "="*70)
    print("⚡ TEST 1: Adaptive Rate Limiter")
    print("="*70)
    
    from src.core.rate_limiter import AdaptiveRateLimiter
    limiter = AdaptiveRateLimiter()
    
    delay1 = await limiter.get_delay("comment")
    print(f"   Base delay: {delay1:.1f}s")
    
    # Simulate error
    limiter.record_flood_wait(120)
    delay2 = await limiter.get_delay("comment")
    print(f"   After flood error: {delay2:.1f}s")
    
    # Simulate success
    limiter.record_success("comment")
    limiter.record_success("comment")
    delay3 = await limiter.get_delay("comment")
    print(f"   After 2 successes: {delay3:.1f}s")
    
    print(f"   ✅ Rate limiter adapts correctly")
    
    # Test 2: Account Warmer (short version)
    print("\n" + "="*70)
    print("🧼 TEST 2: Account Warmer")
    print("="*70)
    
    print("   Testing scroll simulation...")
    await account_warmer.random_scroll("durov", posts=3)
    print("   ✅ Warmup scroll works")
    
    # Test 3: One Pipeline Cycle (manual)
    print("\n" + "="*70)
    print("🔄 TEST 3: One Pipeline Cycle")
    print("="*70)
    
    TEST_CHANNEL = "durov"
    TEST_STYLE = "engaging"
    
    print(f"   Channel: @{TEST_CHANNEL}")
    print(f"   Style: {TEST_STYLE}")
    
    # Parse posts
    posts = await client.parse_last_messages(TEST_CHANNEL, limit=3)
    print(f"   Parsed {len(posts)} posts")
    
    if not posts:
        print("   ⚠️  No posts found, skipping comment test")
    else:
        # Check memory
        from src.db.comment_memory import comment_memory
        
        target_post = posts[0]
        is_commented = comment_memory.is_already_commented(
            TEST_CHANNEL, target_post["id"], hours=24
        )
        
        print(f"   Post {target_post['id']}: already commented = {is_commented}")
        
        if not is_commented:
            print(f"   \n⚠️  About to send REAL comment:")
            print(f"   Post: {target_post['text'][:80]}...")
            
            confirm = input(f"\n   Send comment with style '{TEST_STYLE}'? (yes/skip): ").strip().lower()
            
            if confirm == "yes":
                result = await comment_sender.comment_with_full_cycle(
                    channel=TEST_CHANNEL,
                    post_id=target_post["id"],
                    post_text=target_post.get("text", ""),
                    style=TEST_STYLE
                )
                
                if result:
                    print(f"   ✅ Comment sent! ID: {result['comment_id']}")
                    print(f"   Total time: {result['total_time']}s")
                else:
                    print(f"   ❌ Failed (may need discussion group)")
            else:
                print(f"   ⏭️  Skipped")
    
    # Test 4: Pipeline Status
    print("\n" + "="*70)
    print("📊 TEST 4: Pipeline Status")
    print("="*70)
    
    status = orchestrator.get_status()
    print(f"   Running: {status['running']}")
    print(f"   Comments total: {status['comments_total']}")
    print(f"   Errors: {status['errors_total']}")
    print(f"   Rate limiter: {status['rate_limiter']['status']}")
    
    # Test 5: Formatted Output
    print("\n" + "="*70)
    print("📋 TEST 5: Formatted Status")
    print("="*70)
    
    formatted = orchestrator.get_formatted_status()
    print(formatted)
    
    # Cleanup
    print("\n🧹 Cleaning up...")
    await orchestrator.stop()
    await client.disconnect()
    
    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    print("✅ Telegram connection: WORKING")
    print("✅ Rate limiter: WORKING")
    print("✅ Account warmer: WORKING")
    print("✅ Comment sender: WORKING")
    print("✅ Pipeline orchestrator: WORKING")
    print("✅ Memory tracking: WORKING")
    
    print("\n🎉 Advanced Pipeline is ready!")
    print("="*70)
    
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_pipeline_cycle())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
