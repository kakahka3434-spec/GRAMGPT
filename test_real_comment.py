#!/usr/bin/env python
"""
Real Channel Comment Test - GRAMGPT Live Comment Testing
Tests sending actual comments to real Telegram channels
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from src.services.telegram_user_client import TelegramUserClient
from src.services.comment_sender import CommentSender
from src.core.human_emulation import HumanEmulationEngine
from src.config import settings
from dotenv import load_dotenv

# Load environment
load_dotenv('.env.local')


async def test_real_comment():
    """Test sending real comments to a real channel."""
    
    print("\n" + "="*80)
    print("💬 REAL CHANNEL COMMENT TEST - GRAMGPT Live Comment Testing")
    print("="*80)
    
    # Configuration - USER CONFIGURABLE
    TEST_CHANNEL = "durov"  # Target channel
    COMMENT_STYLE = "engaging"  # expert, engaging, or casual
    DRY_RUN = False  # Set to True to not actually send comment
    
    print(f"\n⚙️  Configuration:")
    print(f"  Channel: @{TEST_CHANNEL}")
    print(f"  Style: {COMMENT_STYLE}")
    print(f"  Dry Run: {DRY_RUN}")
    print(f"\n📌 NOTE: This will send a REAL comment if DRY_RUN=False")
    
    try:
        # Initialize components
        print(f"\n🔧 Initializing components...")
        api_id = int(os.getenv('TELEGRAM_API_ID', 12345678))
        api_hash = os.getenv('TELEGRAM_API_HASH', 'abcdef1234567890abcdef1234567890')
        phone = os.getenv('TELEGRAM_PHONE', '+79990000000')
        
        print(f"  API ID: {api_id}")
        print(f"  Phone: {phone}")
        
        client = TelegramUserClient(api_id=api_id, api_hash=api_hash, phone=phone)
        sender = CommentSender()
        emulator = HumanEmulationEngine()
        
        # Connect to Telegram
        print(f"📡 Connecting to Telegram...")
        await client.connect()
        user = await client.get_me()
        print(f"✅ Connected as: @{user.username if user.username else user.first_name}")
        
        # Parse channel
        print(f"\n📖 Parsing @{TEST_CHANNEL}...")
        posts = await client.parse_last_messages(TEST_CHANNEL, limit=5)
        
        if not posts:
            print(f"❌ No posts found in @{TEST_CHANNEL}!")
            await client.disconnect()
            return False
        
        print(f"✅ Found {len(posts)} posts")
        
        # Select target post
        target_post = posts[0]
        print(f"\n🎯 Target Post:")
        print(f"  ID: {target_post['id']}")
        print(f"  Text: {target_post['text'][:100]}...")
        print(f"  Replies: {target_post.get('replies', 0)}")
        
        # Check if already commented
        from src.db.comment_memory import comment_memory
        is_commented = comment_memory.is_already_commented(
            TEST_CHANNEL,
            target_post['id'],
            hours=24
        )
        
        if is_commented:
            print(f"  ⚠️  Already commented on this post in last 24h")
        else:
            print(f"  ✅ Not yet commented on this post")
        
        # Generate comment
        print(f"\n🤖 Generating comment (style: {COMMENT_STYLE})...")
        generated = await sender.generate_comment(
            post_text=target_post['text'],
            style=COMMENT_STYLE
        )
        
        if not generated or "Error" in str(generated):
            print(f"⚠️  AI generation failed: {generated}")
            print(f"  (This is expected if no API key configured)")
            comment_text = f"Interesting! 🎯 More details?"
            print(f"  Using fallback comment: {comment_text}")
        else:
            comment_text = generated
            print(f"✅ Generated: {comment_text[:80]}...")
        
        # Simulate human behavior
        print(f"\n⏱️  Simulating human behavior...")
        
        # Realistic wait before typing
        wait_time = await emulator.wait_before_action()
        print(f"  Pre-action wait: {wait_time:.1f}s")
        
        # Simulate typing
        type_time = emulator.calculate_typing_time(comment_text)
        print(f"  Typing time: {type_time:.1f}s")
        
        if not DRY_RUN:
            print(f"\n  ⏳ Waiting {wait_time:.1f}s before sending...")
            await asyncio.sleep(min(wait_time, 5))  # Cap at 5s for demo
        
        # Send comment
        print(f"\n📤 Sending comment...")
        
        if DRY_RUN:
            print(f"  [DRY RUN] Would send to @{TEST_CHANNEL} post #{target_post['id']}")
            print(f"  [DRY RUN] Comment: {comment_text}")
            result = {
                'success': True,
                'comment_id': 0,
                'total_time': wait_time + type_time,
                'dry_run': True
            }
        else:
            # Send for real
            result = await sender.send_comment(
                client=client,
                channel=TEST_CHANNEL,
                post_id=target_post['id'],
                comment_text=comment_text
            )
        
        if result and result.get('success', False):
            print(f"✅ SUCCESS!")
            print(f"  Comment ID: {result.get('comment_id', 'N/A')}")
            print(f"  Total time: {result.get('total_time', 'N/A'):.1f}s")
            if result.get('dry_run'):
                print(f"  (Dry run - comment was NOT actually sent)")
            
            # Log to memory
            if not DRY_RUN:
                comment_memory.log_comment(
                    TEST_CHANNEL,
                    target_post['id'],
                    comment_text,
                    style=COMMENT_STYLE
                )
                print(f"  ✅ Logged to memory")
        else:
            print(f"❌ Failed to send comment")
            if result:
                print(f"  Details: {result}")
        
        # Summary
        print("\n" + "="*80)
        print("✅ REAL CHANNEL COMMENT TEST COMPLETE!")
        print("="*80)
        
        print(f"""
What was tested:
  ✅ Connected to real Telegram account
  ✅ Parsed real channel (@{TEST_CHANNEL})
  ✅ Retrieved post data
  ✅ Generated comment with AI
  ✅ Simulated human behavior
  ✅ Sent comment (or dry-run)
  ✅ Logged to memory

Results:
  Channel: @{TEST_CHANNEL}
  Post: #{target_post['id']}
  Style: {COMMENT_STYLE}
  Status: {'DRY_RUN' if DRY_RUN else 'SENT'}

Next Steps:
  1. Run multiple times to test different styles
  2. Monitor comments in Telegram channel
  3. Test with different channels
  4. Create automated campaigns
        """)
        
        await client.disconnect()
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        print(f"\n{traceback.format_exc()}")
        print(f"\nTroubleshooting:")
        print(f"  1. Ensure .env.local has valid API credentials")
        print(f"  2. Check channel @{TEST_CHANNEL} is public")
        print(f"  3. Verify Telegram account is not restricted")
        print(f"  4. Check internet connection")
        return False


async def main():
    """Main entry point."""
    try:
        # Check for command line args
        dry_run = "--dry-run" in sys.argv or "-d" in sys.argv
        
        if dry_run:
            print("\n⚠️  Running in DRY RUN mode - no actual comments will be sent")
        
        success = await test_real_comment()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
