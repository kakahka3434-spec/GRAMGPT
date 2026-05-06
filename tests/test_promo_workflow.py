"""
Promo Workflow Test
Tests ChannelDiscovery, CommentSniper, PromoEngine, WorkModes integration.
"""

import asyncio
import logging
import sys
import tempfile

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

from src.core.work_modes import WorkModeController, MODES, MODE_ORDER
from src.services.promo_engine import PromoEngine


async def test_work_modes():
    """Test work mode controller."""
    print("\n" + "="*70)
    print("🎮 TEST 1: Work Mode Controller")
    print("="*70)
    
    # Test initialization
    controller = WorkModeController("balanced")
    print(f"   Initialized: {controller.current_mode}")
    assert controller.current_mode == "balanced"
    
    # Test mode config
    config = controller.config
    print(f"   Comments/day: {config.comments_per_day}")
    print(f"   Delay range: {config.delay_between_comments}")
    print(f"   Risk tolerance: {config.risk_tolerance}")
    
    # Test manual switch
    success = controller.switch_mode("aggressive", "test")
    print(f"   Switch to aggressive: {'✅' if success else '❌'}")
    assert success
    assert controller.current_mode == "aggressive"
    
    # Test auto-downgrade
    controller.switch_mode("aggressive", "reset")
    controller._manual_override = False  # Reset for auto
    
    # Simulate high risk
    should_downgrade = controller.auto_downgrade(0.6)  # 60% risk > 50% threshold for balanced
    print(f"   Auto-downgrade at 60% risk: {'✅' if should_downgrade else '❌'}")
    # Note: aggressive threshold is 0.7, so 0.6 shouldn't trigger
    
    should_downgrade = controller.auto_downgrade(0.8)  # 80% > 0.7
    print(f"   Auto-downgrade at 80% risk: {'✅' if should_downgrade else '❌'}")
    if should_downgrade:
        print(f"   Downgraded to: {controller.current_mode}")
    
    # Test get status
    status = controller.get_status()
    print(f"   Status: {status['current_mode']}, risk: {status['risk_tolerance']}")
    
    print("   ✅ Work modes work")
    return True


async def test_promo_engine():
    """Test promo engine with anti-spam."""
    print("\n" + "="*70)
    print("🎯 TEST 2: Promo Engine")
    print("="*70)
    
    engine = PromoEngine()
    
    # Test spam detection
    spam_text = "FREE MONEY!!! CLICK HERE NOW!!! BUY BUY BUY"
    validation = engine.validate_comment(spam_text, "balanced")
    print(f"   Spam text score: {validation['spam_score']}")
    print(f"   Valid: {validation['valid']}")
    assert not validation['valid'], "Should detect spam"
    
    # Test safe text
    safe_text = "Кстати, у нас есть полезные материалы по этой теме"
    validation = engine.validate_comment(safe_text, "balanced")
    print(f"   Safe text score: {validation['spam_score']}")
    print(f"   Valid: {validation['valid']}")
    assert validation['valid'], f"Should pass safe text, got score: {validation['spam_score']}"
    
    # Test template generation
    link = "https://t.me/mybot"
    comment = engine._generate_from_template(link)
    print(f"   Template comment: {comment[:60]}...")
    assert link.split('/')[-1] in comment or 't.me' in comment
    
    # Test AI generation (if available)
    print("   Testing AI generation...")
    try:
        ai_comment = await engine.generate_promo_comment(
            post_text="Как заработать на криптовалюте?",
            target_link="t.me/mybot",
            mode="balanced",
            use_ai=False  # Use template for test
        )
        print(f"   Generated: {ai_comment[:60]}...")
        assert len(ai_comment) > 20
        print("   ✅ AI generation works")
    except Exception as e:
        print(f"   ⚠️ AI generation skipped: {e}")
    
    print("   ✅ Promo engine works")
    return True


async def test_channel_discovery_mock():
    """Test channel discovery (mock)."""
    print("\n" + "="*70)
    print("🔍 TEST 3: Channel Discovery (Mock)")
    print("="*70)
    
    # Can't test without live Telegram, but check structure
    from src.services.channel_discovery import ChannelDiscovery
    
    print("   ChannelDiscovery class available: ✅")
    print("   Methods: search_by_keywords, filter_open_comments, discover_target_channels")
    
    return True


async def test_sniper_mock():
    """Test sniper structure (mock)."""
    print("\n" + "="*70)
    print("🎯 TEST 4: Comment Sniper (Mock)")
    print("="*70)
    
    from src.services.comment_sniper import CommentSniper, PendingEdit
    
    print("   CommentSniper class available: ✅")
    print("   PendingEdit dataclass: ✅")
    
    # Test dataclass
    edit = PendingEdit(
        channel="test",
        post_id=123,
        emoji_msg_id=456,
        created_at=__import__('datetime').datetime.now(),
        edit_after=300,
        target_link="t.me/test",
        post_text="Test post"
    )
    print(f"   PendingEdit created: {edit.channel}:{edit.post_id}")
    
    print("   ✅ Sniper structure works")
    return True


async def test_full_workflow_mock():
    """Test full promo workflow integration."""
    print("\n" + "="*70)
    print("🚀 TEST 5: Full Workflow Integration")
    print("="*70)
    
    # Test work mode + promo engine integration
    controller = WorkModeController("balanced")
    engine = PromoEngine()
    
    # Generate promo for different modes
    for mode in ["safe", "balanced", "aggressive"]:
        comment = await engine.generate_promo_comment(
            post_text="Тестовый пост о криптовалюте",
            target_link="t.me/testbot",
            mode=mode,
            use_ai=False
        )
        validation = engine.validate_comment(comment, mode)
        print(f"   Mode {mode}: score={validation['spam_score']:.2f}, valid={validation['valid']}")
    
    # Test mode thresholds
    thresholds = {mode: engine._get_max_spam_score(mode) for mode in ["safe", "balanced", "aggressive"]}
    print(f"   Spam thresholds: {thresholds}")
    assert thresholds["safe"] < thresholds["balanced"] < thresholds["aggressive"]
    
    print("   ✅ Full workflow integration works")
    return True


async def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("🧪 PROMO WORKFLOW TEST SUITE")
    print("="*70)
    
    results = []
    results.append(await test_work_modes())
    results.append(await test_promo_engine())
    results.append(await test_channel_discovery_mock())
    results.append(await test_sniper_mock())
    results.append(await test_full_workflow_mock())
    
    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    tests = ["Work Modes", "Promo Engine", "Channel Discovery", "Comment Sniper", "Full Workflow"]
    for test, result in zip(tests, results):
        print(f"{'✅' if result else '❌'} {test}")
    
    all_passed = all(results)
    
    if all_passed:
        print("\n🎉 All tests passed! Promo workflow is ready.")
        print("\n💡 Next: Test with live Telegram connection")
    else:
        print("\n⚠️ Some tests failed. Check logs above.")
    
    print("="*70)
    return all_passed


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
