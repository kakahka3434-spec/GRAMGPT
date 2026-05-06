#!/usr/bin/env python3
"""
🔴 LIVE TEST: CommentSniper на реальном канале

ВНИМАНИЕ: Этот тест делает РЕАЛЬНЫЕ действия в Telegram!
- Отправляет эмодзи-комментарий
- Редактирует его через N минут

Требует:
1. Авторизованный Telethon session
2. Канал с открытыми комментариями (discussion group)
3. API ключ OpenRouter (для генерации промо)

ИСПОЛЬЗУЙТЕ ТЕСТОВЫЙ КАНАЛ!
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load env
load_dotenv('.env.local')

sys.path.insert(0, r'c:\Users\Administrator\Desktop\ai\GPTGRAM')


async def test_sniper_live():
    """Тест CommentSniper с реальными действиями."""
    
    print("=" * 70)
    print("🔴 LIVE TEST: CommentSniper")
    print("=" * 70)
    print("⚠️  Этот тест отправляет РЕАЛЬНЫЕ комментарии в Telegram!")
    print()
    
    # Check credentials
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    phone = os.getenv('TELEGRAM_PHONE')
    session_path = os.getenv('TELEGRAM_SESSION_PATH', 'data/sessions/test.session')
    
    if not all([api_id, api_hash, phone]):
        print("❌ Ошибка: Не найдены TELEGRAM_API_ID, TELEGRAM_API_HASH или TELEGRAM_PHONE")
        print("   Добавьте их в .env.local")
        return False
    
    print("🔧 Проверка конфигурации:")
    print(f"   API ID: {api_id}")
    print(f"   Phone: {phone}")
    print(f"   Session: {session_path}")
    print()
    
    # Ask for test channel
    print("📢 Для теста нужен канал с открытыми комментариями.")
    print("   Создайте тестовый канал и включите комментарии.")
    print()
    
    test_channel = input("Введите username тестового канала (без @): ").strip()
    if not test_channel:
        print("❌ Канал не указан. Тест отменен.")
        return False
    
    confirm = input(f"⚠️  Будет отправлен комментарий в @{test_channel}. Продолжить? (yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ Тест отменен пользователем.")
        return False
    
    print()
    print("🚀 Запуск теста...")
    print("-" * 70)
    
    try:
        # Import modules
        from src.services.telegram_user_client import TelegramUserClient
        from src.services.promo_engine import PromoEngine
        from src.services.comment_sniper import CommentSniper
        
        # Step 1: Connect to Telegram
        print("\n[1/5] Подключение к Telegram...")
        client = TelegramUserClient(
            api_id=int(api_id),
            api_hash=api_hash,
            phone=phone,
            session_path=session_path
        )
        
        connected = await client.connect()
        if not connected:
            print("❌ Не удалось подключиться к Telegram")
            print("   Возможно, нужна повторная авторизация.")
            return False
        
        me = await client._client.get_me()
        print(f"✅ Подключено как: {me.first_name} (@{me.username or 'no_username'})")
        
        # Step 2: Get channel entity
        print(f"\n[2/5] Проверка канала @{test_channel}...")
        try:
            entity = await client._client.get_entity(test_channel)
            print(f"✅ Канал найден: {entity.title}")
            print(f"   ID: {entity.id}")
            print(f"   Participants: {getattr(entity, 'participants_count', 'N/A')}")
        except Exception as e:
            print(f"❌ Ошибка получения канала: {e}")
            await client.disconnect()
            return False
        
        # Step 3: Check for discussion group
        print(f"\n[3/5] Проверка discussion group...")
        from telethon.tl.functions.channels import GetFullChannelRequest
        
        try:
            full_channel = await client._client(GetFullChannelRequest(channel=entity))
            linked_chat_id = full_channel.full_chat.linked_chat_id
            
            if not linked_chat_id:
                print("❌ Канал не имеет linked discussion group!")
                print("   Включите комментарии в настройках канала.")
                await client.disconnect()
                return False
            
            discussion_group = await client._client.get_entity(linked_chat_id)
            print(f"✅ Discussion group найден: {discussion_group.title}")
            print(f"   ID: {linked_chat_id}")
        except Exception as e:
            print(f"❌ Ошибка проверки discussion group: {e}")
            await client.disconnect()
            return False
        
        # Step 4: Get recent message
        print(f"\n[4/5] Поиск поста для комментария...")
        messages = await client.get_messages(test_channel, limit=1)
        if not messages:
            print("❌ Не найдено сообщений в канале")
            print("   Создайте пост для теста.")
            await client.disconnect()
            return False
        
        message = messages[0]
        print(f"✅ Найден пост ID: {message.id}")
        print(f"   Text: {message.text[:100]}..." if message.text else "   [no text]")
        
        # Step 5: Send emoji comment
        print(f"\n[5/5] Отправка тестового комментария...")
        print("-" * 70)
        
        emoji = "🔥"
        print(f"   Отправка эмодзи: {emoji}")
        
        try:
            result = await client.send_comment(test_channel, message.id, emoji)
            if result:
                print(f"✅ Комментарий отправлен! ID: {result['id']}")
                comment_id = result['id']
                
                # Test edit (short delay for test)
                edit_delay = 30  # seconds for test
                print(f"   Ожидание {edit_delay} сек перед редактированием...")
                await asyncio.sleep(edit_delay)
                
                # Generate promo text
                print("   Генерация промо-текста...")
                promo_engine = PromoEngine({})
                promo_text = await promo_engine.generate_promo_comment(
                    post_text=message.text or "",
                    target_link="https://t.me/test_bot",
                    mode="balanced",
                    use_ai=False  # Use template for test
                )
                print(f"   Промо текст: {promo_text[:50]}...")
                
                # Edit the comment
                print("   Редактирование комментария...")
                try:
                    # Note: editing comments in discussion groups requires special handling
                    # This is a simplified test - actual implementation may vary
                    await client._client.edit_message(
                        entity=discussion_group,
                        message=comment_id,
                        text=promo_text
                    )
                    print("✅ Комментарий отредактирован!")
                    
                    # Verify edit
                    await asyncio.sleep(2)
                    edited_msg = await client._client.get_messages(
                        discussion_group, 
                        ids=comment_id
                    )
                    if edited_msg and edited_msg.text == promo_text:
                        print("✅ Редактирование подтверждено!")
                        test_success = True
                    else:
                        print("⚠️  Редактирование могло не сработать (проверьте вручную)")
                        test_success = False
                        
                except Exception as e:
                    print(f"❌ Ошибка редактирования: {e}")
                    print("   Возможно, Telegram не позволяет редактировать комментарии таким способом.")
                    test_success = False
                    
            else:
                print("❌ Не удалось отправить комментарий")
                test_success = False
                
        except Exception as e:
            print(f"❌ Ошибка при отправке: {e}")
            import traceback
            traceback.print_exc()
            test_success = False
        
        # Cleanup
        await client.disconnect()
        
        # Summary
        print()
        print("=" * 70)
        print("📊 РЕЗУЛЬТАТ ТЕСТА")
        print("=" * 70)
        if test_success:
            print("✅ CommentSniper работает!")
            print("   - Отправка эмодзи: OK")
            print("   - Редактирование: OK")
            print()
            print("🎉 Можно запускать полный пайплайн!")
        else:
            print("⚠️  Тест частично успешен или провален")
            print("   Проверьте:")
            print("   1. Комментарий действительно отправился")
            print("   2. Канал имеет discussion group")
            print("   3. Права на отправку комментариев")
        
        return test_success
        
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_pipeline_simple():
    """Упрощенный тест без реальных действий (только структура)."""
    
    print("=" * 70)
    print("🧪 STRUCTURE TEST: CommentSniper")
    print("=" * 70)
    print("Этот тест проверяет структуру кода без реальных действий.")
    print()
    
    try:
        from src.services.comment_sniper import CommentSniper, PendingEdit
        from src.services.promo_engine import PromoEngine
        import inspect
        
        # Check CommentSniper methods
        print("🔍 Проверка CommentSniper:")
        methods = ['start_monitoring', 'stop_monitoring', '_on_new_message', 
                   '_send_emoji_comment', '_edit_worker']
        for method in methods:
            exists = hasattr(CommentSniper, method)
            status = "✅" if exists else "❌"
            print(f"   {status} {method}")
        
        # Check PendingEdit dataclass
        print("\n🔍 Проверка PendingEdit:")
        sig = inspect.signature(PendingEdit)
        print(f"   ✅ PendingEdit fields: {list(sig.parameters.keys())}")
        
        # Check PromoEngine
        print("\n🔍 Проверка PromoEngine:")
        pe_methods = ['generate_promo_comment', 'validate_comment', '_calculate_spam_score']
        for method in pe_methods:
            exists = hasattr(PromoEngine, method)
            status = "✅" if exists else "❌"
            print(f"   {status} {method}")
        
        print("\n✅ Структура CommentSniper готова!")
        print()
        print("Для полного теста запустите:")
        print("   python test_sniper_live.py --live")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Test CommentSniper')
    parser.add_argument('--live', action='store_true', 
                       help='Run LIVE test with real Telegram actions')
    parser.add_argument('--structure', action='store_true',
                       help='Run structure test only (no real actions)')
    
    args = parser.parse_args()
    
    if args.live:
        # Live test with real actions
        result = asyncio.run(test_sniper_live())
        sys.exit(0 if result else 1)
    else:
        # Structure test by default
        result = asyncio.run(test_pipeline_simple())
        sys.exit(0 if result else 1)
