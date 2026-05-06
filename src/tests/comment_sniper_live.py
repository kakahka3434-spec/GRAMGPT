#!/usr/bin/env python3
"""
🔴 LIVE TEST: CommentSniper в реальном Telegram

⚠️ ВНИМАНИЕ: Этот скрипт делает РЕАЛЬНЫЕ действия в Telegram!
- Отправляет комментарии
- Редактирует их

Используйте ТОЛЬКО на своих тестовых каналах!

Перед запуском:
1. Создайте тестовый канал с discussion group
2. Добавьте бот/аккаунт в админы
3. Убедитесь что у аккаунта есть права на комментирование

ENV переменные:
- TEST_API_ID - Telegram API ID
- TEST_API_HASH - Telegram API Hash  
- TEST_PHONE - Номер телефона (+79990000000)
- TEST_CHANNEL - Username тестового канала (без @)
- TEST_SESSION_PATH - Путь к .session файлу
"""

import asyncio
import os
import sys
import time
from datetime import datetime
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load test environment
load_dotenv('.env.local')

sys.path.insert(0, r'c:\Users\Administrator\Desktop\ai\GPTGRAM')


class LiveTestReporter:
    """Форматированный отчёт о тесте."""
    
    def __init__(self):
        self.results = []
        self.start_time = time.time()
    
    def log(self, status: str, message: str, details: str = ""):
        """Логирование с таймстемпом."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        elapsed = f"T+{time.time() - self.start_time:.1f}s"
        
        emoji = {
            "INFO": "ℹ️",
            "OK": "✅",
            "WARN": "⚠️",
            "FAIL": "❌",
            "STEP": "🔄"
        }.get(status, "•")
        
        line = f"[{timestamp} | {elapsed}] {emoji} [{status}] {message}"
        if details:
            line += f"\n   Details: {details}"
        
        print(line)
        self.results.append({
            "timestamp": timestamp,
            "elapsed": elapsed,
            "status": status,
            "message": message,
            "details": details
        })
    
    def summary(self) -> Dict[str, Any]:
        """Итоговый отчёт."""
        ok_count = sum(1 for r in self.results if r["status"] == "OK")
        fail_count = sum(1 for r in self.results if r["status"] == "FAIL")
        warn_count = sum(1 for r in self.results if r["status"] == "WARN")
        
        return {
            "total_tests": len(self.results),
            "passed": ok_count,
            "failed": fail_count,
            "warnings": warn_count,
            "duration_sec": round(time.time() - self.start_time, 1),
            "results": self.results
        }
    
    def print_summary(self):
        """Печать итогового отчёта."""
        summary = self.summary()
        
        print("\n" + "=" * 70)
        print("📊 LIVE TEST SUMMARY")
        print("=" * 70)
        print(f"✅ Passed: {summary['passed']}")
        print(f"❌ Failed: {summary['failed']}")
        print(f"⚠️  Warnings: {summary['warnings']}")
        print(f"⏱️  Duration: {summary['duration_sec']}s")
        
        if summary['failed'] == 0 and summary['warnings'] == 0:
            print("\n🎉 CommentSniper: PRODUCTION READY")
        elif summary['failed'] == 0:
            print("\n⚠️  CommentSniper: WORKING (with warnings)")
        else:
            print("\n❌ CommentSniper: NEEDS FIXES")
            print("\n❌ Failed tests:")
            for r in summary['results']:
                if r['status'] == 'FAIL':
                    print(f"   - {r['message']}: {r['details']}")
        
        print("=" * 70)


class CommentSniperLiveTest:
    """Live тест CommentSniper."""
    
    def __init__(self):
        self.reporter = LiveTestReporter()
        self.client = None
        self.sniper = None
        self.test_message_id = None
        self.emoji_message_id = None
        
        # Config from ENV
        self.api_id = int(os.getenv('TEST_API_ID', 0))
        self.api_hash = os.getenv('TEST_API_HASH', '')
        self.phone = os.getenv('TEST_PHONE', '')
        self.channel = os.getenv('TEST_CHANNEL', '')
        self.session_path = os.getenv('TEST_SESSION_PATH', 'data/sessions/test_live.session')
        
        # Validation
        self._validate_config()
    
    def _validate_config(self):
        """Проверка конфигурации."""
        missing = []
        if not self.api_id:
            missing.append('TEST_API_ID')
        if not self.api_hash:
            missing.append('TEST_API_HASH')
        if not self.phone:
            missing.append('TEST_PHONE')
        if not self.channel:
            missing.append('TEST_CHANNEL')
        
        if missing:
            self.reporter.log("FAIL", "Missing ENV variables", ", ".join(missing))
            print("\n📋 Required ENV:")
            print("   TEST_API_ID=123456")
            print("   TEST_API_HASH=abcdef...")
            print("   TEST_PHONE=+79990000000")
            print("   TEST_CHANNEL=my_test_channel")
            print("   TEST_SESSION_PATH=data/sessions/test.session")
            sys.exit(1)
    
    async def setup(self):
        """Шаг 1: Подготовка и подключение."""
        self.reporter.log("STEP", "Step 1: Setup & Connection")
        
        from src.services.telegram_user_client import TelegramUserClient
        from src.services.promo_engine import PromoEngine
        from src.services.comment_sniper import CommentSniper
        from src.core.work_modes import WorkModeController
        
        # Create client
        self.reporter.log("INFO", "Creating Telegram client", f"session={self.session_path}")
        self.client = TelegramUserClient(
            api_id=self.api_id,
            api_hash=self.api_hash,
            phone=self.phone,
            session_path=self.session_path
        )
        
        # Connect
        self.reporter.log("INFO", "Connecting to Telegram...")
        try:
            connected = await asyncio.wait_for(self.client.connect(), timeout=30.0)
            if not connected:
                self.reporter.log("FAIL", "Failed to connect to Telegram")
                return False
        except asyncio.TimeoutError:
            self.reporter.log("FAIL", "Connection timeout", "30s exceeded")
            return False
        
        # Verify identity
        me = await self.client._client.get_me()
        self.reporter.log("OK", f"Connected as @{me.username}", f"ID: {me.id}")
        
        # Verify channel access
        try:
            entity = await self.client._client.get_entity(self.channel)
            self.reporter.log("OK", f"Channel access confirmed", f"@{self.channel} - {entity.title}")
        except Exception as e:
            self.reporter.log("FAIL", "Cannot access test channel", str(e))
            self.reporter.log("INFO", "Make sure you:")
            self.reporter.log("INFO", "  1. Created a channel with discussion group")
            self.reporter.log("INFO", "  2. Added this account as admin")
            return False
        
        # Create sniper with Balanced mode (edit delay 180-300s)
        promo_engine = PromoEngine({})
        self.sniper = CommentSniper(
            telegram_client=self.client,
            promo_engine=promo_engine,
            settings={"target_link": "https://t.me/test_bot"}
        )
        
        # Apply work mode settings
        mode_controller = WorkModeController("balanced")
        mode_controller.apply_to_sniper(self.sniper)
        
        self.reporter.log("OK", "CommentSniper initialized", f"Mode: balanced, Edit delay: {self.sniper.settings.get('edit_delay_min', 180)}-{self.sniper.settings.get('edit_delay_max', 300)}s")
        
        return True
    
    async def run_scenario(self):
        """Шаг 2: Основной сценарий теста."""
        self.reporter.log("STEP", "Step 2: Main Test Scenario")
        
        # Start monitoring
        self.reporter.log("INFO", "Starting CommentSniper monitoring", f"Channel: @{self.channel}")
        await self.sniper.start_monitoring(
            channels=[self.channel],
            edit_delay_range=(30, 60),  # Shortened for test (normally 180-300)
            target_link="https://t.me/test_bot"
        )
        
        if not self.sniper._monitoring:
            self.reporter.log("FAIL", "Sniper failed to start monitoring")
            return False
        
        self.reporter.log("OK", "Sniper monitoring active")
        
        # Wait for sniper to be ready
        await asyncio.sleep(2)
        
        # Publish test post or use existing
        self.reporter.log("INFO", "Publishing test post...")
        
        try:
            from telethon.tl.types import InputMediaPhoto
            
            # Simple text post
            post_text = f"🧪 Live test post #sniper_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            message = await self.client._client.send_message(
                self.channel,
                post_text
            )
            self.test_message_id = message.id
            
            t0 = time.time()
            self.reporter.log("OK", f"Test post published", f"Message ID: {message.id}, T0={t0:.3f}")
            
        except Exception as e:
            self.reporter.log("FAIL", "Failed to publish test post", str(e))
            return False
        
        # Wait for emoji comment (up to 10 seconds)
        self.reporter.log("INFO", "Waiting for emoji comment...")
        
        emoji_found = False
        emoji_sent_time = None
        
        for i in range(20):  # 20 * 0.5s = 10s
            await asyncio.sleep(0.5)
            
            # Check sniper stats
            status = self.sniper.get_status()
            if status["emoji_sent"] > 0 and not emoji_found:
                emoji_found = True
                emoji_sent_time = time.time()
                delay = emoji_sent_time - t0
                self.reporter.log("OK", f"Emoji comment sent", f"Delay: {delay:.1f}s (target: <5s)")
                
                if delay <= 5.0:
                    self.reporter.log("OK", "Emoji delay within target")
                else:
                    self.reporter.log("WARN", "Emoji delay too high", f"{delay:.1f}s > 5s")
                
                break
        
        if not emoji_found:
            self.reporter.log("FAIL", "Emoji comment not detected")
            return False
        
        # Wait for edit (shortened 30-60s for test)
        self.reporter.log("INFO", "Waiting for edit to promo...", f"Edit window: 30-60s")
        
        edit_found = False
        max_wait = 70  # seconds
        
        for i in range(max_wait):
            await asyncio.sleep(1)
            
            # Check sniper stats
            status = self.sniper.get_status()
            if status["edits_completed"] > 0 and not edit_found:
                edit_found = True
                edit_time = time.time()
                total_delay = edit_time - t0
                
                self.reporter.log("OK", f"Edit completed", f"Total delay: {total_delay:.1f}s")
                
                # Validate delay is in expected range
                if 25 <= total_delay <= 70:  # 30-60s + margin
                    self.reporter.log("OK", "Edit delay within target range")
                else:
                    self.reporter.log("WARN", "Edit delay outside target", 
                                     f"Expected 30-60s, got {total_delay:.1f}s")
                
                break
        
        if not edit_found:
            self.reporter.log("FAIL", "Edit not completed within timeout", f"Waited {max_wait}s")
            return False
        
        return True
    
    async def test_edge_cases(self):
        """Шаг 3: Проверка крайних случаев."""
        self.reporter.log("STEP", "Step 3: Edge Case Tests")
        
        # Test 1: Get sniper status
        try:
            status = self.sniper.get_status()
            self.reporter.log("OK", "Sniper status retrieved", 
                             f"Posts seen: {status['posts_seen']}, Emoji sent: {status['emoji_sent']}, Edits: {status['edits_completed']}")
        except Exception as e:
            self.reporter.log("WARN", "Could not get sniper status", str(e))
        
        # Test 2: Stop and restart monitoring
        try:
            await self.sniper.stop_monitoring()
            self.reporter.log("OK", "Sniper stopped successfully")
            
            # Verify stopped
            if not self.sniper._monitoring:
                self.reporter.log("OK", "Monitoring state confirmed: stopped")
            else:
                self.reporter.log("WARN", "Monitoring state still active after stop")
        except Exception as e:
            self.reporter.log("WARN", "Error stopping sniper", str(e))
        
        return True
    
    async def cleanup(self):
        """Очистка после теста."""
        self.reporter.log("STEP", "Cleanup")
        
        try:
            if self.sniper and self.sniper._monitoring:
                await self.sniper.stop_monitoring()
                self.reporter.log("OK", "Sniper stopped")
        except Exception as e:
            self.reporter.log("WARN", "Error during sniper cleanup", str(e))
        
        try:
            if self.client:
                await self.client.disconnect()
                self.reporter.log("OK", "Telegram client disconnected")
        except Exception as e:
            self.reporter.log("WARN", "Error during client cleanup", str(e))
    
    async def run(self):
        """Главный метод запуска теста."""
        print("=" * 70)
        print("🔴 COMMENTSNIPER LIVE TEST")
        print("=" * 70)
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📱 Test Channel: @{self.channel}")
        print(f"⚠️  WARNING: This will send REAL comments to Telegram!")
        print("=" * 70)
        
        # Confirm test channel
        confirm = input(f"\n⚠️  Confirm test channel @{self.channel}? (yes/no): ")
        if confirm.lower() != 'yes':
            print("❌ Test cancelled by user")
            return False
        
        try:
            # Step 1: Setup
            if not await self.setup():
                self.reporter.log("FAIL", "Setup failed, aborting test")
                return False
            
            # Step 2: Main scenario
            if not await self.run_scenario():
                self.reporter.log("FAIL", "Main scenario failed")
            
            # Step 3: Edge cases
            await self.test_edge_cases()
            
        except Exception as e:
            self.reporter.log("FAIL", "Unexpected error during test", str(e))
            import traceback
            traceback.print_exc()
            
        finally:
            # Cleanup
            await self.cleanup()
            
            # Print summary
            self.reporter.print_summary()
            
            # Save report to file
            report_file = f"data/sniper_live_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            try:
                import json
                os.makedirs("data", exist_ok=True)
                with open(report_file, 'w') as f:
                    json.dump(self.reporter.summary(), f, indent=2, ensure_ascii=False)
                print(f"\n📝 Full report saved to: {report_file}")
            except Exception as e:
                print(f"\n⚠️  Could not save report: {e}")
        
        # Return success if no failures
        summary = self.reporter.summary()
        return summary['failed'] == 0


async def main():
    """Entry point."""
    test = CommentSniperLiveTest()
    success = await test.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
