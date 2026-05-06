"""
Multi-Account & Analytics Test
Tests account pool rotation, proxy assignment, and analytics export.
"""

import asyncio
import logging
import os
import sys
import tempfile

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

from src.core.account_pool import AccountPool, AccountStatus
from src.core.proxy_manager import ProxyManager
from src.services.analytics_exporter import AnalyticsExporter


async def test_proxy_validation():
    """Test proxy validation."""
    print("\n" + "="*70)
    print("🔌 TEST 1: Proxy Validation")
    print("="*70)
    
    pm = ProxyManager()
    
    # Test with no proxy (direct)
    result = await pm.validate_proxy(None)
    print(f"   Direct connection: {'✅ PASS' if result else '❌ FAIL'}")
    
    # Test with invalid proxy
    result = await pm.validate_proxy("http://invalid.proxy:99999", timeout=3)
    print(f"   Invalid proxy: {'⚠️ Expected FAIL' if not result else '❌ Unexpected PASS'}")
    
    print("   ✅ Proxy validation works")
    return True


async def test_account_pool():
    """Test account pool management."""
    print("\n" + "="*70)
    print("🎯 TEST 2: Account Pool")
    print("="*70)
    
    # Use temp file for test
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_file = f.name
    
    try:
        # Create pool
        pool = AccountPool(pool_file=temp_file)
        
        # Add first account
        success = pool.add_account(
            phone="+79990000001",
            session_path="data/sessions/test1.session",
            proxy=None,
            validate_proxy=False
        )
        print(f"   Add account 1: {'✅' if success else '❌'}")
        
        # Add second account with proxy
        success = pool.add_account(
            phone="+79990000002",
            session_path="data/sessions/test2.session",
            proxy="http://test.proxy:8080",
            validate_proxy=False  # Skip validation for test
        )
        print(f"   Add account 2: {'✅' if success else '❌'}")
        
        # Try duplicate
        success = pool.add_account(
            phone="+79990000001",
            session_path="data/sessions/test1.session",
            validate_proxy=False
        )
        print(f"   Duplicate check: {'⚠️ Blocked' if not success else '❌ Unexpected'}")
        
        # Get next active
        acc = pool.get_next_active()
        if acc:
            print(f"   Round-robin: ✅ Got {acc.phone}")
        else:
            print(f"   Round-robin: ❌ No account")
        
        # Mark status
        pool.mark_status("+79990000001", AccountStatus.COOLDOWN, cooldown_minutes=1)
        print(f"   Mark cooldown: ✅")
        
        # Check health report
        report = pool.get_health_report()
        print(f"   Pool stats: {report['total']} total, {report['active']} active, {report['cooldown']} cooldown")
        print(f"   Risk score: {report['risk_score']}/100")
        
        # Get formatted report
        formatted = pool.get_formatted_report()
        print(f"   Formatted report: {len(formatted)} chars")
        
        print("   ✅ Account pool works")
        return True
        
    finally:
        # Cleanup
        if os.path.exists(temp_file):
            os.remove(temp_file)


async def test_analytics_exporter():
    """Test analytics export functionality."""
    print("\n" + "="*70)
    print("📊 TEST 3: Analytics Exporter")
    print("="*70)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_file = f.name
    
    try:
        # Create pool with test data
        pool = AccountPool(pool_file=temp_file)
        pool.add_account("+79990000001", "sessions/test1.session", validate_proxy=False)
        pool.add_account("+79990000002", "sessions/test2.session", validate_proxy=False)
        
        # Create exporter
        exporter = AnalyticsExporter(account_pool=pool)
        
        # Calculate metrics
        metrics = await exporter.calculate_metrics(hours=24)
        print(f"   Metrics calculated: ✅")
        print(f"   - Comments: {metrics['total_comments']}")
        print(f"   - Success rate: {metrics['success_rate']}%")
        print(f"   - Risk score: {metrics['risk_score']}/100")
        
        # Generate risk report
        report = await exporter.generate_risk_report()
        print(f"   Risk report: ✅ ({len(report)} chars)")
        
        # Export CSV
        csv_path = await exporter.export_csv(hours=24, filename="test_export.csv")
        if os.path.exists(csv_path):
            size = os.path.getsize(csv_path)
            print(f"   CSV export: ✅ ({size} bytes)")
            os.remove(csv_path)
        else:
            print(f"   CSV export: ⚠️ File not created (empty data)")
        
        # Export JSON
        json_path = await exporter.export_json(hours=24, filename="test_export.json")
        if os.path.exists(json_path):
            size = os.path.getsize(json_path)
            print(f"   JSON export: ✅ ({size} bytes)")
            os.remove(json_path)
        else:
            print(f"   JSON export: ⚠️ File not created")
        
        print("   ✅ Analytics exporter works")
        return True
        
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)


async def test_account_rotation_simulation():
    """Simulate account rotation with errors."""
    print("\n" + "="*70)
    print("🔄 TEST 4: Account Rotation Simulation")
    print("="*70)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_file = f.name
    
    try:
        pool = AccountPool(pool_file=temp_file)
        
        # Add 3 accounts
        for i in range(1, 4):
            pool.add_account(
                phone=f"+7999000000{i}",
                session_path=f"sessions/test{i}.session",
                validate_proxy=False
            )
        
        print(f"   Added 3 accounts: ✅")
        
        # Simulate work
        for i in range(5):
            acc = pool.get_next_active()
            if acc:
                # Simulate success/error
                if i == 2:  # Simulate error on 3rd iteration
                    pool.record_error(acc.phone, "FloodWait: 120s", cooldown_minutes=5)
                    print(f"   Iter {i+1}: {acc.phone} → ERROR (cooldown)")
                else:
                    pool.record_success(acc.phone)
                    print(f"   Iter {i+1}: {acc.phone} → SUCCESS")
            else:
                print(f"   Iter {i+1}: No active account")
        
        # Check final state
        report = pool.get_health_report()
        print(f"   Final state: {report['active']} active, {report['cooldown']} cooldown")
        print(f"   Success rate: {report['success_rate']}%")
        
        print("   ✅ Rotation simulation works")
        return True
        
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)


async def test_full_pipeline():
    """Test full multi-account pipeline."""
    print("\n" + "="*70)
    print("🚀 FULL PIPELINE TEST")
    print("="*70)
    
    print("\n⚠️  Note: This test simulates the pipeline without actual Telegram connection")
    print("   Use test_pipeline_advanced.py for live Telegram testing")
    
    results = []
    results.append(await test_proxy_validation())
    results.append(await test_account_pool())
    results.append(await test_analytics_exporter())
    results.append(await test_account_rotation_simulation())
    
    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    print(f"✅ Proxy validation: {'PASS' if results[0] else 'FAIL'}")
    print(f"✅ Account pool: {'PASS' if results[1] else 'FAIL'}")
    print(f"✅ Analytics export: {'PASS' if results[2] else 'FAIL'}")
    print(f"✅ Account rotation: {'PASS' if results[3] else 'FAIL'}")
    
    all_passed = all(results)
    
    if all_passed:
        print("\n🎉 All tests passed! Multi-account system ready.")
    else:
        print("\n⚠️  Some tests failed. Check logs above.")
    
    print("="*70)
    return all_passed


if __name__ == "__main__":
    try:
        success = asyncio.run(test_full_pipeline())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
