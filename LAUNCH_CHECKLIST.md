# GRAMGPT — Чеклист запуска

## 🎯 Миссия: Проверить что реально работает

---

## ЧАСТЬ 1: Подготовка (5 минут)

### 1.1 Проверка файлов
```bash
# Проверь что все файлы на месте
ls data/sessions/           # Должен быть хотя бы 1 .session файл
ls src/core/                # Все core модули
ls src/services/            # Все service модули
```

### 1.2 Переменные окружения
Создай `.env.local`:
```bash
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_PHONE=+79990000000
TELEGRAM_SESSION_PATH=data/sessions/main.session

# Для CommentSniper теста
OPENROUTER_API_KEY=sk-or-v1-...  # или другой AI ключ

# Опционально
PROXY_URL=socks5://user:pass@host:port
```

### 1.3 Проверка зависимостей
```bash
pip list | grep -E "telethon|aiogram|aiohttp"
# Должно быть:
# aiogram        3.x
# aiohttp        3.x
# Telethon       1.x
```

---

## ЧАСТЬ 2: Структурные тесты (2 минуты)

### 2.1 Базовый импорт
```bash
python -c "from src.services.telegram_user_client import TelegramUserClient; print('✅')"
python -c "from src.services.comment_sender import CommentSender; print('✅')"
python -c "from src.services.comment_sniper import CommentSniper; print('✅')"
python -c "from src.services.promo_engine import PromoEngine; print('✅')"
python -c "from src.core.pipeline_orchestrator import PipelineOrchestrator; print('✅')"
```

### 2.2 Структура CommentSniper
```bash
python test_sniper_live.py --structure
# Ожидаемый вывод:
# ✅ start_monitoring
# ✅ stop_monitoring
# ✅ _on_new_message
# ✅ _send_emoji_comment
# ✅ _edit_worker
```

---

## ЧАСТЬ 3: Тест с реальным Telegram (10 минут)

### ⚠️ ВНИМАНИЕ: Эти тесты делают РЕАЛЬНЫЕ действия!

### 3.1 Подключение
```python
python -c "
import asyncio
from src.services.telegram_user_client import TelegramUserClient
from dotenv import load_dotenv
import os
load_dotenv('.env.local')

async def test():
    client = TelegramUserClient(
        api_id=int(os.getenv('TELEGRAM_API_ID')),
        api_hash=os.getenv('TELEGRAM_API_HASH'),
        phone=os.getenv('TELEGRAM_PHONE'),
        session_path=os.getenv('TELEGRAM_SESSION_PATH')
    )
    result = await client.connect()
    print(f'Подключение: {result}')
    if result:
        me = await client._client.get_me()
        print(f'Аккаунт: @{me.username}')
    await client.disconnect()

asyncio.run(test())
"
```

**✅ PASS:** Подключение успешно, виден username

### 3.2 Отправка комментария
```python
# ВАЖНО: Используй тестовый канал!
TEST_CHANNEL = "your_test_channel"  # Без @
TEST_MESSAGE_ID = 1  # ID поста

python -c "
import asyncio
import os
from dotenv import load_dotenv
load_dotenv('.env.local')

from src.services.telegram_user_client import TelegramUserClient

async def test():
    client = TelegramUserClient(
        api_id=int(os.getenv('TELEGRAM_API_ID')),
        api_hash=os.getenv('TELEGRAM_API_HASH'),
        phone=os.getenv('TELEGRAM_PHONE'),
        session_path=os.getenv('TELEGRAM_SESSION_PATH')
    )
    await client.connect()
    
    # Отправка
    result = await client.send_comment('TEST_CHANNEL', TEST_MESSAGE_ID, '🔥 Test')
    print(f'Результат: {result}')
    
    await client.disconnect()

asyncio.run(test())
"
```

**✅ PASS:** Комментарий появился в канале (проверь вручную)

### 3.3 Проверка discussion group
```python
python -c "
import asyncio
import os
from dotenv import load_dotenv
load_dotenv('.env.local')

from src.services.telegram_user_client import TelegramUserClient
from telethon.tl.functions.channels import GetFullChannelRequest

async def test():
    client = TelegramUserClient(...)
    await client.connect()
    
    entity = await client._client.get_entity('TEST_CHANNEL')
    full = await client._client(GetFullChannelRequest(channel=entity))
    
    linked = full.full_chat.linked_chat_id
    print(f'Linked chat ID: {linked}')
    print(f'Комментарии {"включены" if linked else "ОТКЛЮЧЕНЫ"}')
    
    await client.disconnect()

asyncio.run(test())
"
```

**✅ PASS:** `linked_chat_id` не None

### 3.4 Полный тест CommentSniper
```bash
# Запускаем интерактивный тест
python test_sniper_live.py --live
```

**✅ PASS:**
- Эмодзи отправлен
- Отредактирован в промо
- Подтверждено проверкой

---

## ЧАСТЬ 4: Интеграционный тест (30 минут)

### 4.1 Запуск PipelineOrchestrator
```python
python -c "
import asyncio
import os
from dotenv import load_dotenv
load_dotenv('.env.local')

from src.core.pipeline_orchestrator import PipelineOrchestrator
from src.services.telegram_user_client import TelegramUserClient

async def test():
    # Создаем клиент
    telegram = TelegramUserClient(...)
    
    # Создаем оркестратор
    from src.services.comment_sender import CommentSender
    sender = CommentSender(telegram)
    
    orchestrator = PipelineOrchestrator(
        telegram_client=telegram,
        comment_sender=sender
    )
    
    # Запускаем на 5 минут
    await orchestrator.start(
        target_channels=['TEST_CHANNEL'],
        style='balanced',
        max_comments_per_hour=2
    )
    
    # Ждем 5 минут
    await asyncio.sleep(300)
    
    # Останавливаем
    await orchestrator.stop()
    
    # Статистика
    print(orchestrator.get_status_report())

asyncio.run(test())
"
```

**✅ PASS:**
- Пайплайн запустился без ошибок
- Отправлено 0-1 комментариев (в зависимости от постов)
- Graceful shutdown работает
- Статистика собрана

---

## ЧАСТЬ 5: Проверка мульти-аккаунта (10 минут)

### 5.1 AccountPool
```python
python -c "
from src.core.account_pool import AccountPool, AccountStatus

pool = AccountPool(pool_file='data/test_pool.json')

# Добавляем тестовый аккаунт
pool.add_account(
    phone='+79990000001',
    session_path='data/sessions/test.session',
    proxy=None,
    validate_proxy=False
)

# Проверяем
acc = pool.get_next_active()
print(f'Аккаунт: {acc.phone if acc else None}')

# Статус
pool.mark_status(acc.phone, AccountStatus.COOLDOWN, cooldown_minutes=5)

# Отчет
print(pool.get_health_report())
"
```

**✅ PASS:**
- Аккаунт добавлен
- Round-robin работает
- Cooldown выставляется
- Отчет генерируется

---

## ЧАСТЬ 6: Прокси (опционально, 5 минут)

### 6.1 Валидация
```python
python -c "
import asyncio
from src.core.proxy_manager import ProxyManager

async def test():
    pm = ProxyManager()
    
    # Тест прокси (замени на свой)
    proxy = 'socks5://user:pass@host:port'
    result = await pm.validate_proxy(proxy, timeout=10)
    print(f'Прокси {proxy}: {result}')

asyncio.run(test())
"
```

**✅ PASS:** Прокси валиден (или нет — тоже полезная информация)

---

## 📊 ИТОГОВЫЙ ЧЕКЛИСТ

| # | Тест | Статус | Комментарий |
|---|------|--------|-------------|
| 1 | Подключение Telegram | ⬜ | |
| 2 | Отправка комментария | ⬜ | |
| 3 | Discussion group check | ⬜ | |
| 4 | CommentSniper live | ⬜ | |
| 5 | PipelineOrchestrator 5min | ⬜ | |
| 6 | AccountPool | ⬜ | |
| 7 | Proxy validation | ⬜ | Опционально |

**Если все ✅ → Готово к продакшену!**

**Если есть ❌ → Нужна доработка**

---

## 🚨 Частые проблемы

### Проблема: "Session not found"
**Решение:**
```bash
# Авторизация заново
python -c "
from telethon import TelegramClient
client = TelegramClient('data/sessions/main', API_ID, 'API_HASH')
client.start()
# Введи код из Telegram
"
```

### Проблема: "Channel has no discussion group"
**Решение:**
1. В канале → Settings → Discussion
2. Включи "Enable discussion"
3. Выбери или создай группу

### Проблема: "FloodWaitError"
**Решение:**
- Подожди указанное время
- Используй прокси
- Перейди в режим `reliable`

---

## 🎯 Далее

После прохождения всех тестов:
1. **Создайте бота** в @BotFather
2. **Добавьте команды** из `COMMANDS.md`
3. **Настройте вебхук** (опционально)
4. **Запустите полный цикл** на 24 часа

**Успехов! 🚀**
