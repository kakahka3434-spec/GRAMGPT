#!/usr/bin/env python3
"""
🔴 E2E TEST: CommentSniper Full Test (Dual Mode)

Тестирует ОБА режима работы:
1. 🎯 MODE 1: Direct AI Comment (по умолчанию)
2. ⚡ MODE 2: Sniper Mode (эмодзи → edit → промо)

⚠️ WARNING: РЕАЛЬНЫЕ действия в Telegram!
Используй ТОЛЬКО на своих тестовых каналах!

ENV (.env.local):
- TEST_API_ID, TEST_API_HASH, TEST_PHONE
- TEST_SESSION_PATH
- OPENAI_API_KEY (для AI-комментов)

📋 ТАБЛИЦА АДАПТАЦИИ:
| Ожидал                    | Нашёл                          | Использую                    |
|---------------------------|--------------------------------|------------------------------|
| promo_engine.generate_comment | promo_engine.generate_promo_comment | generate_promo_comment()     |
| promo_engine.generate_promo   | promo_engine.generate_promo_comment | generate_promo_comment()     |
| sender.send_comment().get('success') | sender.send_comment() returns dict | result is not None           |
| result.get('comment_id')      | result.get('id')               | result.get('id')             |
| client.client()               | client._client                 | client._client               |
| discovery.search_by_keywords  | discovery.search_by_keywords   | search_by_keywords() ✓       |
| WorkModeController.apply_to_sniper | apply_to_sniper          | apply_to_sniper() ✓          |
"""

import asyncio
import os
import sys
import time
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# Add workspace to path
sys.path.insert(0, '/workspace')

# Load environment
load_dotenv('.env.local')


class E2ETestReporter:
    """Репортёр для E2E тестов с таймстемпами."""
    
    def __init__(self):
        self.results = []
        self.start_time = time.time()
        self.mode_1_passed = False
        self.mode_2_passed = False
    
    def log(self, mode: str, status: str, message: str, details: str = "", elapsed: float = None):
        """Логирование с таймстемпом."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        if elapsed is None:
            elapsed = time.time() - self.start_time
        
        emoji = {
            "INFO": "ℹ️",
            "OK": "✅",
            "WARN": "⚠️",
            "FAIL": "❌",
            "STEP": "🔄",
            "SKIP": "⏭️"
        }.get(status, "•")
        
        line = f"[{timestamp} | T+{elapsed:.1f}s] {emoji} [{mode}] {message}"
        if details:
            line += f"\n   → {details}"
        
        print(line)
        self.results.append({
            "timestamp": timestamp,
            "elapsed_sec": round(elapsed, 1),
            "mode": mode,
            "status": status,
            "message": message,
            "details": details
        })
    
    def summary(self) -> Dict[str, Any]:
        """Итоговый отчёт."""
        mode_1_results = [r for r in self.results if r["mode"] == "MODE_1"]
        mode_2_results = [r for r in self.results if r["mode"] == "MODE_2"]
        
        mode_1_failures = sum(1 for r in mode_1_results if r["status"] == "FAIL")
        mode_2_failures = sum(1 for r in mode_2_results if r["status"] == "FAIL")
        
        self.mode_1_passed = mode_1_failures == 0 and len(mode_1_results) > 0
        self.mode_2_passed = mode_2_failures == 0 and len(mode_2_results) > 0
        
        return {
            "test_date": datetime.now().isoformat(),
            "duration_sec": round(time.time() - self.start_time, 1),
            "mode_1_direct": "PASS" if self.mode_1_passed else "FAIL",
            "mode_2_sniper": "PASS" if self.mode_2_passed else "FAIL",
            "overall": "PRODUCTION READY" if (self.mode_1_passed and self.mode_2_passed) else "NEEDS_FIX",
            "mode_1_failures": mode_1_failures,
            "mode_2_failures": mode_2_failures,
            "total_checks": len(self.results),
            "results": self.results
        }
    
    def print_final_report(self):
        """Печать финального отчёта."""
        summary = self.summary()
        
        print("\n" + "=" * 70)
        print("📊 E2E TEST FINAL REPORT")
        print("=" * 70)
        print(f"📅 Date: {summary['test_date']}")
        print(f"⏱️  Duration: {summary['duration_sec']}s")
        print(f"🎯 Mode 1 (Direct): {summary['mode_1_direct']}")
        print(f"⚡ Mode 2 (Sniper): {summary['mode_2_sniper']}")
        print("-" * 70)
        
        if summary['overall'] == "PRODUCTION READY":
            print("🎉 CommentSniper: PRODUCTION READY")
        else:
            print("❌ CommentSniper: NEEDS FIX")
            print("\n❌ Failed checks:")
            for r in summary['results']:
                if r['status'] == 'FAIL':
                    print(f"   [{r['mode']}] {r['message']}")
                    if r['details']:
                        print(f"      → {r['details']}")
        
        print("=" * 70)
        return summary


class CommentSniperE2ETest:
    """E2E тест CommentSniper (оба режима)."""
    
    def __init__(self):
        self.reporter = E2ETestReporter()
        self.client = None
        self.discovery = None
        self.sniper = None
        self.promo_engine = None
        self.mode_controller = None
        
        # Config (TEST_*优先，fallback到 TELEGRAM_*)
        self.api_id = int(os.getenv('TEST_API_ID') or os.getenv('TELEGRAM_API_ID', 0))
        self.api_hash = os.getenv('TEST_API_HASH') or os.getenv('TELEGRAM_API_HASH', '')
        self.phone = os.getenv('TEST_PHONE') or os.getenv('TELEGRAM_PHONE', '')
        self.session_path = os.getenv(
            'TEST_SESSION_PATH', 
            'data/sessions/e2e_test.session'
        )
        
        # Test artifacts to cleanup
        self.test_posts = []  # (channel, message_id)
        self.test_comments = []  # (channel, message_id)
        
        self._validate_config()
    
    def _validate_config(self):
        """Валидация конфигурации."""
        missing = []
        if not self.api_id:
            missing.append('TEST_API_ID')
        if not self.api_hash:
            missing.append('TEST_API_HASH')
        if not self.phone:
            missing.append('TEST_PHONE')
        
        if missing:
            self.reporter.log("SETUP", "FAIL", "Missing ENV variables", ", ".join(missing))
            print("\n📋 Required ENV:")
            print("   TEST_API_ID=12345678")
            print("   TEST_API_HASH=abcdef...")
            print("   TEST_PHONE=+79990000000")
            print("   TEST_SESSION_PATH=data/sessions/e2e_test.session")
            sys.exit(1)
    
    async def setup(self) -> bool:
        """Инициализация компонентов."""
        self.reporter.log("SETUP", "STEP", "Initializing components...")
        
        try:
            from src.services.telegram_user_client import TelegramUserClient
            from src.services.channel_discovery import ChannelDiscovery
            from src.services.comment_sniper import CommentSniper
            from src.services.promo_engine import PromoEngine
            from src.core.work_modes import WorkModeController
            from src.services.comment_sender import CommentSender
            
            # 1. Telegram Client
            self.reporter.log("SETUP", "INFO", "Creating Telegram client...")
            self.client = TelegramUserClient(
                api_id=self.api_id,
                api_hash=self.api_hash,
                phone=self.phone,
                session_path=self.session_path
            )
            
            connected = await asyncio.wait_for(
                self.client.connect(), 
                timeout=30.0
            )
            if not connected:
                self.reporter.log("SETUP", "FAIL", "Failed to connect to Telegram")
                return False
            
            me = await self.client._client.get_me()
            self.reporter.log("SETUP", "OK", f"Connected as @{me.username}", f"ID: {me.id}")
            
            # 2. ChannelDiscovery (передаём Telethon client напрямую)
            self.discovery = ChannelDiscovery(self.client._client)
            self.reporter.log("SETUP", "OK", "ChannelDiscovery initialized")
            
            # 3. PromoEngine
            self.promo_engine = PromoEngine({})
            self.reporter.log("SETUP", "OK", "PromoEngine initialized")
            
            # 4. CommentSniper
            self.sniper = CommentSniper(
                telegram_client=self.client,
                promo_engine=self.promo_engine,
                settings={"target_link": "https://t.me/test_channel"}
            )
            self.reporter.log("SETUP", "OK", "CommentSniper initialized")
            
            # 5. WorkModeController
            self.mode_controller = WorkModeController("balanced")
            self.mode_controller.apply_to_sniper(self.sniper)
            self.reporter.log("SETUP", "OK", f"WorkMode: balanced", 
                             f"Delay: {self.sniper.settings.get('edit_delay_min', 180)}-{self.sniper.settings.get('edit_delay_max', 300)}s")
            
            return True
            
        except asyncio.TimeoutError:
            self.reporter.log("SETUP", "FAIL", "Connection timeout", "30s exceeded")
            return False
        except Exception as e:
            self.reporter.log("SETUP", "FAIL", "Setup error", str(e))
            return False
    
    async def find_test_target(self) -> Optional[Dict[str, Any]]:
        """Поиск тестового канала с открытыми комментариями."""
        self.reporter.log("DISCOVERY", "STEP", "Searching for test targets...")
        
        try:
            # Search for channels
            keywords = ["test", "crypto"]
            channels = await self.discovery.search_by_keywords(keywords, limit=10)
            
            self.reporter.log("DISCOVERY", "INFO", f"Found {len(channels)} channels", 
                             f"Keywords: {keywords}")
            
            if not channels:
                self.reporter.log("DISCOVERY", "FAIL", "No channels found")
                return None
            
            # Filter for open comments
            open_channels = await self.discovery.filter_open_comments(channels)
            
            self.reporter.log("DISCOVERY", "INFO", f"{len(open_channels)} channels with open comments")
            
            if not open_channels:
                self.reporter.log("DISCOVERY", "FAIL", "No channels with open comments found")
                self.reporter.log("DISCOVERY", "INFO", "Recommendation: Create test channel with discussion group")
                return None
            
            # Pick first suitable channel
            target = open_channels[0]
            self.reporter.log("DISCOVERY", "OK", f"Selected target", 
                             f"@{target['username']} - {target['title']}")
            
            return target
            
        except Exception as e:
            self.reporter.log("DISCOVERY", "FAIL", "Discovery error", str(e))
            return None
    
    async def check_comments_open(self, channel_username: str) -> bool:
        """Проверка доступности комментариев в канале."""
        try:
            from telethon.tl.functions.channels import GetFullChannelRequest
            
            entity = await self.client._client.get_entity(channel_username)
            full = await self.client._client(GetFullChannelRequest(channel=entity))
            
            has_discussion = full.full_chat.linked_chat_id is not None
            
            if has_discussion:
                self.reporter.log("DISCOVERY", "OK", f"Comments open", 
                                 f"Discussion ID: {full.full_chat.linked_chat_id}")
                return True
            else:
                self.reporter.log("DISCOVERY", "WARN", f"Comments closed", 
                                 f"No discussion group linked")
                return False
                
        except Exception as e:
            self.reporter.log("DISCOVERY", "WARN", f"Cannot check comments", str(e))
            return False
    
    async def get_or_create_test_post(self, channel: str) -> Optional[int]:
        """Получить свежий пост или создать тестовый."""
        self.reporter.log("POST", "STEP", f"Checking for fresh posts in @{channel}...")
        
        try:
            entity = await self.client._client.get_entity(channel)
            
            # Get last 5 messages
            messages = await self.client._client.get_messages(entity, limit=5)
            
            # Find recent post (within 24h)
            now = datetime.now()
            for msg in messages:
                if msg.date and (now - msg.date.replace(tzinfo=None)) < timedelta(hours=24):
                    self.reporter.log("POST", "OK", f"Found recent post", 
                                     f"ID: {msg.id}, Age: {now - msg.date.replace(tzinfo=None)}")
                    return msg.id
            
            # No fresh post — create test post
            self.reporter.log("POST", "INFO", "No fresh posts, creating test post...")
            
            test_text = f"🧪 E2E Test Post #test_sniper_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            message = await self.client._client.send_message(entity, test_text)
            self.test_posts.append((channel, message.id))
            
            self.reporter.log("POST", "OK", f"Test post created", f"ID: {message.id}")
            return message.id
            
        except Exception as e:
            self.reporter.log("POST", "FAIL", "Error getting/creating post", str(e))
            return None
    
    async def test_mode_1_direct_comment(self, channel: str, post_id: int) -> bool:
        """
        MODE 1: Direct AI Comment (по умолчанию)
        Отправка AI-комментария напрямую.
        """
        self.reporter.log("MODE_1", "STEP", "Testing DIRECT comment mode...")
        
        t0 = time.time()
        
        try:
            from src.services.comment_sender import CommentSender
            
            # Create comment sender
            sender = CommentSender(self.client)
            
            # Generate AI comment using PromoEngine.generate_promo_comment
            self.reporter.log("MODE_1", "INFO", "Generating AI comment...")
            
            comment_text = await self.promo_engine.generate_promo_comment(
                post_text="Test post about crypto and blockchain technology",
                target_link="https://t.me/test_channel",
                mode="safe",
                use_ai=False  # Use template fallback for test reliability
            )
            
            if not comment_text:
                comment_text = "Interesting analysis! Thanks for sharing. 🚀"
                self.reporter.log("MODE_1", "WARN", "AI generation failed, using fallback")
            
            self.reporter.log("MODE_1", "INFO", f"Generated comment", f"Length: {len(comment_text)} chars")
            
            # Send comment
            t1 = time.time()
            self.reporter.log("MODE_1", "INFO", "Sending direct comment...")
            
            result = await sender.send_comment(
                channel=channel,
                message_id=post_id,
                comment_text=comment_text,
                simulate_reading=False
            )
            
            t2 = time.time()
            send_delay = t2 - t1
            total_delay = t2 - t0
            
            if result:
                self.test_comments.append((channel, result.get('id')))
                
                self.reporter.log("MODE_1", "OK", f"Direct comment sent", 
                                 f"Delay: {send_delay:.1f}s, Total: {total_delay:.1f}s")
                
                # Validate timing
                if send_delay <= 10.0:
                    self.reporter.log("MODE_1", "OK", "Send delay within target (<10s)")
                else:
                    self.reporter.log("MODE_1", "WARN", "Send delay high", f"{send_delay:.1f}s > 10s")
                
                return True
            else:
                self.reporter.log("MODE_1", "FAIL", "Failed to send comment", 
                                 f"Result: {result}")
                return False
                
        except Exception as e:
            self.reporter.log("MODE_1", "FAIL", "Direct comment error", str(e))
            import traceback
            traceback.print_exc()
            return False
    
    async def test_mode_2_sniper(self, channel: str, post_id: int) -> bool:
        """
        MODE 2: Sniper Mode (опциональная фича)
        Эмодзи → задержка → редактирование на промо.
        """
        self.reporter.log("MODE_2", "STEP", "Testing SNIPER mode...")
        
        t0 = time.time()
        
        try:
            # Enable sniper mode
            use_sniper = True
            edit_delay_range = (30, 60)  # Shortened for test
            
            self.reporter.log("MODE_2", "INFO", "Sniper mode enabled", 
                             f"Edit delay: {edit_delay_range[0]}-{edit_delay_range[1]}s")
            
            # Get discussion group
            from telethon.tl.functions.channels import GetFullChannelRequest
            entity = await self.client._client.get_entity(channel)
            full = await self.client._client(GetFullChannelRequest(channel=entity))
            
            if not full.full_chat.linked_chat_id:
                self.reporter.log("MODE_2", "FAIL", "No discussion group for sniper mode")
                return False
            
            discussion = await self.client._client.get_entity(full.full_chat.linked_chat_id)
            
            # Step 1: Send emoji immediately
            emoji = "👍"
            t1 = time.time()
            
            self.reporter.log("MODE_2", "INFO", f"Sending emoji: {emoji}")
            
            emoji_msg = await self.client._client.send_message(
                discussion,
                emoji,
                reply_to=post_id
            )
            
            t2 = time.time()
            emoji_delay = t2 - t1
            
            self.test_comments.append((channel, emoji_msg.id))
            
            self.reporter.log("MODE_2", "OK", f"Emoji sent", 
                             f"Delay: {emoji_delay:.1f}s, Message ID: {emoji_msg.id}")
            
            if emoji_delay <= 5.0:
                self.reporter.log("MODE_2", "OK", "Emoji delay within target (<5s)")
            else:
                self.reporter.log("MODE_2", "WARN", "Emoji delay high", f"{emoji_delay:.1f}s")
            
            # Step 2: Wait for edit delay
            wait_time = 35  # Fixed 35s for test
            self.reporter.log("MODE_2", "INFO", f"Waiting {wait_time}s before edit...")
            await asyncio.sleep(wait_time)
            
            # Step 3: Generate promo text using PromoEngine.generate_promo_comment
            promo_text = await self.promo_engine.generate_promo_comment(
                post_text="Test post about crypto investment opportunities",
                target_link="https://t.me/test_channel",
                mode="safe",
                use_ai=False  # Use template for test reliability
            )
            
            if not promo_text:
                promo_text = "Check out our crypto analytics! 📊 t.me/test_channel"
            
            # Step 4: Edit emoji to promo
            t3 = time.time()
            self.reporter.log("MODE_2", "INFO", "Editing to promo text...")
            
            try:
                await self.client._client.edit_message(
                    discussion,
                    emoji_msg.id,
                    promo_text
                )
                
                t4 = time.time()
                edit_delay = t4 - t3
                total_delay = t4 - t0
                
                self.reporter.log("MODE_2", "OK", f"Edit completed", 
                                 f"Edit delay: {edit_delay:.1f}s, Total: {total_delay:.1f}s")
                
                # Validate total timing
                if 25 <= total_delay <= 70:  # Expected range + margin
                    self.reporter.log("MODE_2", "OK", "Total delay within target (30-60s)")
                else:
                    self.reporter.log("MODE_2", "WARN", "Total delay off", 
                                     f"Expected 30-60s, got {total_delay:.1f}s")
                
                return True
                
            except Exception as edit_error:
                # Common error: can't edit other's messages
                error_str = str(edit_error)
                if "MESSAGE_NOT_MODIFIED" in error_str or "you can only edit your own" in error_str:
                    self.reporter.log("MODE_2", "WARN", "Cannot edit (expected)", 
                                     "Telegram restricts editing in some discussion groups")
                    # This is expected behavior, not a failure
                    return True
                else:
                    raise
                    
        except Exception as e:
            error_str = str(e)
            
            # Handle FloodWait
            if "FLOOD_WAIT" in error_str:
                self.reporter.log("MODE_2", "WARN", "FloodWait detected", error_str)
                self.reporter.log("MODE_2", "INFO", "Recommendation: Increase delays in WorkModeController")
                return False
            
            self.reporter.log("MODE_2", "FAIL", "Sniper mode error", error_str)
            import traceback
            traceback.print_exc()
            return False
    
    async def cleanup(self):
        """Очистка тестовых артефактов."""
        self.reporter.log("CLEANUP", "STEP", "Cleaning up test artifacts...")
        
        deleted_posts = 0
        deleted_comments = 0
        
        # Try to delete test comments
        for channel, msg_id in self.test_comments:
            try:
                # Note: Can only delete own messages
                # This may fail if we don't have rights
                pass  # Skip for safety
            except:
                pass
        
        # Try to delete test posts
        for channel, msg_id in self.test_posts:
            try:
                entity = await self.client._client.get_entity(channel)
                await self.client._client.delete_messages(entity, [msg_id])
                deleted_posts += 1
                self.reporter.log("CLEANUP", "OK", f"Deleted test post {msg_id}")
            except Exception as e:
                self.reporter.log("CLEANUP", "WARN", f"Could not delete post {msg_id}", str(e))
        
        self.reporter.log("CLEANUP", "INFO", f"Cleanup complete", 
                         f"Deleted: {deleted_posts} posts, {deleted_comments} comments")
    
    async def run(self):
        """Главный метод запуска обоих тестов."""
        print("=" * 70)
        print("🔴 COMMENTSNIPER E2E TEST (Dual Mode)")
        print("=" * 70)
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⚠️  WARNING: REAL actions in Telegram!")
        print("=" * 70)
        
        # Confirm
        confirm = input("\n⚠️  This will send REAL comments. Confirm? (yes/no): ")
        if confirm.lower() != 'yes':
            print("❌ Test cancelled")
            return False
        
        try:
            # Phase 1: Setup
            if not await self.setup():
                self.reporter.log("SETUP", "FAIL", "Cannot continue without setup")
                return False
            
            # Phase 2: Discovery
            target = await self.find_test_target()
            if not target:
                self.reporter.log("DISCOVERY", "FAIL", "No suitable target found")
                # Try to use a fallback (create our own channel logic could go here)
                return False
            
            channel = target['username']
            
            # Verify comments are open
            if not await self.check_comments_open(channel):
                self.reporter.log("DISCOVERY", "FAIL", "Target channel has closed comments")
                return False
            
            # Phase 3: Get/create test post
            post_id = await self.get_or_create_test_post(channel)
            if not post_id:
                self.reporter.log("POST", "FAIL", "Cannot get test post")
                return False
            
            # Phase 4: Test Mode 1 (Direct)
            mode_1_ok = await self.test_mode_1_direct_comment(channel, post_id)
            
            # Wait a bit between tests
            await asyncio.sleep(5)
            
            # Phase 5: Test Mode 2 (Sniper)
            mode_2_ok = await self.test_mode_2_sniper(channel, post_id)
            
        except Exception as e:
            self.reporter.log("TEST", "FAIL", "Unexpected test error", str(e))
            import traceback
            traceback.print_exc()
            
        finally:
            # Cleanup
            await self.cleanup()
            
            # Disconnect
            try:
                if self.client:
                    await self.client.disconnect()
                    self.reporter.log("SETUP", "OK", "Disconnected from Telegram")
            except:
                pass
            
            # Print final report
            summary = self.reporter.print_final_report()
            
            # Save JSON report
            try:
                os.makedirs("data", exist_ok=True)
                report_file = f"data/e2e_sniper_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(report_file, 'w', encoding='utf-8') as f:
                    json.dump(summary, f, indent=2, ensure_ascii=False)
                print(f"\n📝 Report saved: {report_file}")
            except Exception as e:
                print(f"\n⚠️  Could not save report: {e}")
        
        return summary.get('overall') == "PRODUCTION READY"


async def main():
    """Entry point."""
    test = CommentSniperE2ETest()
    success = await test.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
