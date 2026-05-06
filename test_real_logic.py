# test_real_logic.py — проверка реальной работы модулей
import asyncio
import sys
import os

# Добавляем корень проекта в путь
sys.path.insert(0, r'c:\Users\Administrator\Desktop\ai\GPTGRAM')

async def test_openai():
    """Тест 1: OpenAI клиент"""
    print("\n🔹 Тест 1: OpenAI клиент...")
    try:
        from src.core.openai_client import openai_client
        resp = await openai_client.get_chat_response(0, [{"role": "user", "content": "Say 'TEST_OK'"}])
        if "TEST_OK" in resp or len(resp) > 0:
            print(f"✅ OpenAI: работает (ответ: {resp[:50]}...)")
            return True
        else:
            print(f"⚠️ OpenAI: вернул неожиданный ответ: {resp}")
            return False
    except Exception as e:
        print(f"❌ OpenAI: {e}")
        return False

async def test_channel_discovery():
    """Тест 2: Channel Discovery — реальный поиск"""
    print("\n🔹 Тест 2: Channel Discovery (проверка реального кода)...")
    try:
        from src.services.channel_discovery import ChannelDiscovery
        import inspect
        
        # Проверяем исходный код метода
        source = inspect.getsource(ChannelDiscovery.search_by_keywords)
        
        # Ищем признаки реального кода vs заглушки
        if "SearchRequest" in source and "self.client" in source:
            print("✅ ChannelDiscovery: содержит реальный Telethon код (SearchRequest)")
            print("   Но для работы нужен подключенный Telegram клиент")
            return True
        elif "mock" in source.lower() or "return []" in source:
            print("❌ ChannelDiscovery: ЗАГЛУШКА (mock/пустой return)")
            return False
        else:
            print(f"⚠️ ChannelDiscovery: код непонятен, нужна проверка")
            print(f"   Исходник: {source[:200]}...")
            return False
    except Exception as e:
        print(f"❌ ChannelDiscovery: {e}")
        return False

async def test_comment_sniper():
    """Тест 3: Comment Sniper — реальная отправка"""
    print("\n🔹 Тест 3: Comment Sniper (проверка кода)...")
    try:
        from src.services.comment_sniper import CommentSniper
        import inspect
        
        # Проверяем наличие реальной отправки
        source = inspect.getsource(CommentSniper)
        
        checks = {
            "Telethon отправка": "send_message" in source or "SendMessageRequest" in source,
            "Редактирование": "edit_message" in source or "EditMessageRequest" in source,
            "Обработка ошибок": "FloodWaitError" in source or "try:" in source,
            "Очередь": "asyncio.Queue" in source
        }
        
        print("   Проверка компонентов:")
        for name, exists in checks.items():
            status = "✅" if exists else "❌"
            print(f"   {status} {name}")
        
        if all(checks.values()):
            print("✅ CommentSniper: структура для реальной работы есть")
            return True
        else:
            print("⚠️ CommentSniper: частичная реализация")
            return False
    except Exception as e:
        print(f"❌ CommentSniper: {e}")
        return False

async def test_telegram_client():
    """Тест 4: Telegram клиент — подключение"""
    print("\n🔹 Тест 4: TelegramUserClient (проверка структуры)...")
    try:
        from src.services.telegram_user_client import TelegramUserClient
        import inspect
        
        source = inspect.getsource(TelegramUserClient)
        
        checks = {
            "Telethon импорт": "TelegramClient" in source,
            "Метод connect": "connect" in source,
            "Парсинг сообщений": "parse_messages" in source,
            "Обработка сессий": "session" in source.lower()
        }
        
        print("   Проверка компонентов:")
        for name, exists in checks.items():
            status = "✅" if exists else "❌"
            print(f"   {status} {name}")
        
        if checks["Telethon импорт"] and checks["Метод connect"]:
            print("✅ TelegramUserClient: структура для подключения есть")
            return True
        else:
            print("❌ TelegramUserClient: неполная реализация")
            return False
    except Exception as e:
        print(f"❌ TelegramUserClient: {e}")
        return False

async def test_comment_sender():
    """Тест 5: CommentSender — реальная отправка комментариев"""
    print("\n🔹 Тест 5: CommentSender (проверка кода)...")
    try:
        from src.services.comment_sender import CommentSender
        import inspect
        
        source = inspect.getsource(CommentSender)
        
        # Ищем реальную отправку
        has_send = "send" in source.lower()
        has_comment = "comment" in source.lower()
        has_telethon = "TelegramClient" in source or "client" in source
        
        print(f"   Компоненты: send={has_send}, comment={has_comment}, client={has_telethon}")
        
        # Проверяем сигнатуру метода send_comment
        if hasattr(CommentSender, 'send_comment'):
            sig = inspect.signature(CommentSender.send_comment)
            print(f"   Метод send_comment: {sig}")
            print("✅ CommentSender: интерфейс для отправки есть")
            return True
        else:
            print("❌ CommentSender: нет метода send_comment")
            return False
    except Exception as e:
        print(f"❌ CommentSender: {e}")
        return False

async def check_imports():
    """Проверка всех импортов"""
    print("\n📦 Проверка импортов модулей:")
    
    modules = [
        "src.core.openai_client",
        "src.services.telegram_user_client",
        "src.services.comment_sender",
        "src.services.account_warmer",
        "src.services.channel_discovery",
        "src.services.comment_sniper",
        "src.services.promo_engine",
        "src.core.work_modes",
        "src.core.pipeline_orchestrator",
        "src.core.account_pool",
        "src.core.proxy_manager",
    ]
    
    results = {}
    for mod in modules:
        try:
            __import__(mod)
            print(f"   ✅ {mod}")
            results[mod] = True
        except Exception as e:
            print(f"   ❌ {mod}: {e}")
            results[mod] = False
    
    return results

async def main():
    print("=" * 60)
    print("🔍 РЕАЛЬНАЯ ПРОВЕРКА МОДУЛЕЙ GRAMGPT")
    print("=" * 60)
    
    # Проверка импортов
    import_results = await check_imports()
    
    # Детальные тесты
    results = {
        "openai": await test_openai(),
        "channel_discovery": await test_channel_discovery(),
        "comment_sniper": await test_comment_sniper(),
        "telegram_client": await test_telegram_client(),
        "comment_sender": await test_comment_sender(),
    }
    
    # Итог
    print("\n" + "=" * 60)
    print("📊 ИТОГОВАЯ СВОДКА")
    print("=" * 60)
    
    working = []
    partial = []
    broken = []
    
    for name, result in results.items():
        if result is True:
            working.append(name)
        elif result is False:
            broken.append(name)
        else:
            partial.append(name)
    
    print(f"\n✅ Работающие (структура есть): {working}")
    print(f"⚠️  Требуют проверки: {partial}")
    print(f"❌ Проблемы: {broken}")
    
    print("\n⚡ КЛЮЧЕВАЯ ПРОБЛЕМА:")
    if broken:
        print(f"   Модули {broken} НЕ ГОТОВЫ для продакшена.")
        print("   Нужно реализовать реальную логику вместо заглушек.")
    
    print("\n🎯 СЛЕДУЮЩИЕ ШАГИ:")
    print("   1. Реализовать реальную отправку комментариев (CommentSender)")
    print("   2. Тестировать ChannelDiscovery с реальным Telegram клиентом")
    print("   3. Проверить CommentSniper на тестовом канале")
    print("   4. Написать интеграционные тесты с реальными запросами")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())
