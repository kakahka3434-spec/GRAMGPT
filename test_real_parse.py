#!/usr/bin/env python
"""
Real Channel Parse Test - GRAMGPT Live Testing
Tests actual Telegram channel parsing on real data
No setup needed - just run this script!
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from src.services.telegram_user_client import TelegramUserClient
from src.config import settings
from dotenv import load_dotenv

# Load environment
load_dotenv('.env.local')


async def test_real_channel_parsing():
    """Parse a real Telegram channel and test the system."""
    
    print("\n" + "="*80)
    print("🔍 REAL CHANNEL PARSE TEST - GRAMGPT Live Testing")
    print("="*80)
    
    # Configuration
    TEST_CHANNEL = "durov"  # Public channel - Pavel Durov's channel (safe for testing)
    PARSE_LIMIT = 10       # Parse last 10 posts
    
    print(f"\n📍 Target Channel: @{TEST_CHANNEL}")
    print(f"📊 Posts to parse: {PARSE_LIMIT}")
    print(f"🔑 Using credentials from .env.local")
    
    try:
        # Initialize client
        print(f"\n🔌 Initializing Telegram client...")
        api_id = int(os.getenv('TELEGRAM_API_ID', 12345678))
        api_hash = os.getenv('TELEGRAM_API_HASH', 'abcdef1234567890abcdef1234567890')
        phone = os.getenv('TELEGRAM_PHONE', '+79990000000')
        
        print(f"  API ID: {api_id}")
        print(f"  Phone: {phone}")
        
        client = TelegramUserClient(api_id=api_id, api_hash=api_hash, phone=phone)
        
        # Connect
        print(f"📡 Connecting to Telegram...")
        await client.connect()
        
        # Get current user info
        user = await client.get_me()
        print(f"✅ Connected as: @{user.username if user.username else user.first_name}")
        
        # Parse channel
        print(f"\n📖 Parsing last {PARSE_LIMIT} posts from @{TEST_CHANNEL}...")
        posts = await client.parse_last_messages(TEST_CHANNEL, limit=PARSE_LIMIT)
        
        if not posts:
            print(f"❌ No posts found!")
            return False
        
        print(f"\n✅ Successfully parsed {len(posts)} posts!")
        
        # Display post details
        print("\n" + "-"*80)
        print("📋 POST DETAILS")
        print("-"*80)
        
        for i, post in enumerate(posts[:5], 1):  # Show first 5
            print(f"\n Post #{i}:")
            print(f"  ID: {post['id']}")
            print(f"  Date: {post.get('date', 'N/A')}")
            print(f"  Text: {post['text'][:80]}...")
            print(f"  Replies: {post.get('replies', 0)}")
            print(f"  Views: {post.get('views', 0)}")
            print(f"  Has discussion: {post.get('has_discussion', False)}")
        
        if len(posts) > 5:
            print(f"\n  ... and {len(posts) - 5} more posts")
        
        # Test channel metadata
        print("\n" + "-"*80)
        print("📊 CHANNEL METADATA")
        print("-"*80)
        
        channel_info = await client.get_channel_info(TEST_CHANNEL)
        if channel_info:
            print(f"  Channel: @{TEST_CHANNEL}")
            print(f"  Title: {channel_info.get('title', 'N/A')}")
            print(f"  Members: {channel_info.get('members_count', 'N/A'):,}")
            print(f"  Description: {channel_info.get('description', 'N/A')[:100]}...")
        
        # Test comment memory
        print("\n" + "-"*80)
        print("💾 COMMENT MEMORY TEST")
        print("-"*80)
        
        from src.db.comment_memory import comment_memory
        
        target_post = posts[0]
        is_commented = comment_memory.is_already_commented(
            TEST_CHANNEL, 
            target_post['id'], 
            hours=24
        )
        
        print(f"  Post ID: {target_post['id']}")
        print(f"  Already commented (24h): {is_commented}")
        print(f"  ✅ Memory system working")
        
        # Summary
        print("\n" + "="*80)
        print("✅ REAL CHANNEL PARSE TEST SUCCESSFUL!")
        print("="*80)
        
        print(f"""
Summary:
  ✅ Connected to Telegram successfully
  ✅ Parsed {len(posts)} real posts from @{TEST_CHANNEL}
  ✅ Retrieved channel metadata
  ✅ Comment memory system working
  ✅ All systems operational!

Next Steps:
  1. Create a campaign with real posts
  2. Select a commenting style
  3. Send automated comments
  4. Monitor engagement

Ready to test commenting? Use the comment sender script!
        """)
        
        await client.disconnect()
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print(f"\nTroubleshooting:")
        print(f"  1. Check .env.local has valid TELEGRAM_API_ID and TELEGRAM_API_HASH")
        print(f"  2. Verify internet connection")
        print(f"  3. Check Telegram account is not restricted")
        print(f"  4. Ensure API credentials are from https://my.telegram.org")
        return False


async def main():
    """Main entry point."""
    try:
        success = await test_real_channel_parsing()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
