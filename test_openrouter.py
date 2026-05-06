"""
Test script for OpenRouter AI client.
Verifies the free AI API is working correctly.
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

from src.core.ai_client import ai_client
from src.config import settings


async def test_openrouter():
    """Test OpenRouter connection and chat response."""
    
    print("=" * 60)
    print("🔧 Testing OpenRouter AI Client")
    print("=" * 60)
    
    # Check configuration
    print(f"\n📋 Configuration:")
    print(f"   Provider: {settings.ai_provider}")
    print(f"   Model: {settings.model_name}")
    print(f"   API Key: {'✓ Set' if settings.openrouter_api_key else '✗ Missing'}")
    
    if not settings.openrouter_api_key:
        print("\n❌ ERROR: OpenRouter API key not configured!")
        return False
    
    if settings.ai_provider != "openrouter":
        print(f"\n⚠️  WARNING: AI provider is '{settings.ai_provider}', expected 'openrouter'")
        print("   Check your .env.local file")
    
    # Check client initialization
    print(f"\n🔌 Client Status:")
    if ai_client.client:
        print("   ✓ Client initialized successfully")
        print(f"   ✓ Using provider: {ai_client.provider}")
    else:
        print("   ✗ Client not initialized")
        print("   Possible reasons: missing API key, invalid configuration")
        return False
    
    # Test chat response
    print(f"\n💬 Testing Chat Response:")
    test_messages = [
        {"role": "user", "content": "Привет! Ответь коротко: ты работаешь?"}
    ]
    
    try:
        print("   Sending test message...")
        response = await ai_client.get_chat_response(0, test_messages)
        
        if response.startswith("❌") or response.startswith("⚠️"):
            print(f"   ✗ Error: {response}")
            return False
        
        print(f"   ✓ Response received!")
        print(f"\n📝 AI Response:")
        print(f"   {response[:200]}{'...' if len(response) > 200 else ''}")
        
    except Exception as e:
        print(f"   ✗ Exception: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ OpenRouter test passed! AI is working.")
    print("=" * 60)
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_openrouter())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
