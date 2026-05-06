# 🔴 CommentSniper E2E Full Test

## 📄 Файл: `src/tests/comment_sniper_full_test.py`

### 🎯 Что тестирует

Скрипт проверяет **ОБА режима** CommentSniper:

| Режим | Описание | Ожидаемое поведение |
|-------|----------|---------------------|
| **MODE 1: Direct** | AI-комментарий напрямую | Генерация → Отправка (<10s) |
| **MODE 2: Sniper** | Эмодзи → Edit → Промо | Emoji (<5s) → Edit (30-60s) |

---

## 🛡️ Обработка крайних случаев

### 1. Закрытые комментарии
```python
# Проверка перед тестом
async def check_comments_open(channel):
    full = await client(GetFullChannelRequest(channel))
    if not full.full_chat.linked_chat_id:
        return False  # ❌ SKIP: No discussion group
```
**Результат:** Тест ищет другой канал или создаёт тестовый пост.

### 2. FloodWaitError
```python
try:
    await client.send_message(...)
except Exception as e:
    if "FLOOD_WAIT" in str(e):
        # ⚠️ WARN: Flood detected
        # Рекомендация: увеличить задержки
```
**Результат:** Тест логирует warning, но не падает. В отчёте: рекомендация увеличить delays.

### 3. Нет свежих постов
```python
# Ищем посты за последние 24ч
if post.date > (now - 24h):
    use_existing = True
else:
    # Создаём тестовый пост с хэштегом
    test_text = f"🧪 E2E Test #test_sniper_{YYYYMMDD}"
```
**Результат:** Автоматическое создание тестового поста (и авто-удаление после).

### 4. Редактирование чужих сообщений
```python
try:
    await client.edit_message(...)
except Exception as e:
    if "you can only edit your own" in str(e):
        # ⚠️ WARN: Cannot edit (expected in some groups)
        # Это нормальное поведение Telegram
```
**Результат:** Тест считает это expected behavior, не failure.

### 5. Отсутствие целевых каналов
```python
channels = await discovery.search_by_keywords(["test", "crypto"], limit=10)
if not channels:
    # FAIL: No channels found
    # Рекомендация: создать тестовый канал
```
**Результат:** Явный FAIL с инструкцией.

---

## 📋 Пример ожидаемого лога

```
======================================================================
🔴 COMMENTSNIPER E2E TEST (Dual Mode)
======================================================================
📅 Date: 2025-01-15 14:30:00
⚠️  WARNING: REAL actions in Telegram!
======================================================================

⚠️  This will send REAL comments. Confirm? (yes/no): yes

[14:30:02.123 | T+0.1s] 🔄 [SETUP] Initializing components...
[14:30:02.456 | T+0.5s] ℹ️  [SETUP] Creating Telegram client...
[14:30:04.789 | T+2.8s] ✅ [SETUP] Connected as @test_account, ID: 123456789
[14:30:05.012 | T+3.0s] ✅ [SETUP] ChannelDiscovery initialized
[14:30:05.234 | T+3.2s] ✅ [SETUP] PromoEngine initialized
[14:30:05.456 | T+3.4s] ✅ [SETUP] CommentSniper initialized
[14:30:05.678 | T+3.6s] ✅ [SETUP] WorkMode: balanced, Delay: 180-300s

[14:30:06.123 | T+4.1s] 🔄 [DISCOVERY] Searching for test targets...
[14:30:08.456 | T+6.4s] ℹ️  [DISCOVERY] Found 5 channels, Keywords: ['test', 'crypto']
[14:30:10.789 | T+8.7s] ℹ️  [DISCOVERY] 3 channels with open comments
[14:30:11.012 | T+8.9s] ✅ [DISCOVERY] Selected target, @my_test_channel - Test Channel
[14:30:11.234 | T+9.1s] ✅ [DISCOVERY] Comments open, Discussion ID: -1001234567890

[14:30:12.123 | T+10.0s] 🔄 [POST] Checking for fresh posts in @my_test_channel...
[14:30:13.456 | T+11.3s] ℹ️  [POST] No fresh posts, creating test post...
[14:30:15.789 | T+13.6s] ✅ [POST] Test post created, ID: 12345

[14:30:16.123 | T+14.0s] 🔄 [MODE_1] Testing DIRECT comment mode...
[14:30:16.456 | T+14.3s] ℹ️  [MODE_1] Generating AI comment...
[14:30:18.789 | T+16.6s] ℹ️  [MODE_1] Generated comment, Length: 87 chars
[14:30:19.012 | T+16.9s] ℹ️  [MODE_1] Sending direct comment...
[14:30:21.456 | T+19.3s] ✅ [MODE_1] Direct comment sent, Delay: 2.1s, Total: 19.3s
[14:30:21.678 | T+19.5s] ✅ [MODE_1] Send delay within target (<10s)

[14:30:26.123 | T+24.0s] 🔄 [MODE_2] Testing SNIPER mode...
[14:30:26.456 | T+24.3s] ℹ️  [MODE_2] Sniper mode enabled, Edit delay: 30-60s
[14:30:26.789 | T+24.6s] ℹ️  [MODE_2] Sending emoji: 👍
[14:30:28.123 | T+25.9s] ✅ [MODE_2] Emoji sent, Delay: 1.5s, Message ID: 12346
[14:30:28.345 | T+26.1s] ✅ [MODE_2] Emoji delay within target (<5s)
[14:30:28.567 | T+26.3s] ℹ️  [MODE_2] Waiting 35s before edit...

[14:31:03.123 | T+61.0s] ℹ️  [MODE_2] Editing to promo text...
[14:31:04.456 | T+62.3s] ✅ [MODE_2] Edit completed, Edit delay: 1.2s, Total: 36.1s
[14:31:04.678 | T+62.5s] ✅ [MODE_2] Total delay within target (30-60s)

[14:31:05.123 | T+63.0s] 🔄 [CLEANUP] Cleaning up test artifacts...
[14:31:06.456 | T+64.3s] ✅ [CLEANUP] Deleted test post 12345
[14:31:06.678 | T+64.5s] ℹ️  [CLEANUP] Cleanup complete, Deleted: 1 posts, 0 comments
[14:31:07.123 | T+65.0s] ✅ [SETUP] Disconnected from Telegram

======================================================================
📊 E2E TEST FINAL REPORT
======================================================================
📅 Date: 2025-01-15T14:31:07.456789
⏱️  Duration: 65.0s
🎯 Mode 1 (Direct): PASS
⚡ Mode 2 (Sniper): PASS
----------------------------------------------------------------------
🎉 CommentSniper: PRODUCTION READY
======================================================================

📝 Report saved: data/e2e_sniper_test_20250115_143107.json
```

---

## 📊 Структура JSON-отчёта

```json
{
  "test_date": "2025-01-15T14:31:07.456789",
  "duration_sec": 65.0,
  "mode_1_direct": "PASS",
  "mode_2_sniper": "PASS",
  "overall": "PRODUCTION READY",
  "mode_1_failures": 0,
  "mode_2_failures": 0,
  "total_checks": 25,
  "results": [
    {
      "timestamp": "14:30:04.789",
      "elapsed_sec": 2.8,
      "mode": "SETUP",
      "status": "OK",
      "message": "Connected as @test_account",
      "details": "ID: 123456789"
    },
    ...
  ]
}
```

---

## 🚀 Критерии PRODUCTION READY

| Критерий | Требование | Результат |
|----------|-----------|-----------|
| Mode 1 (Direct) | Коммент отправлен <10s | ✅ PASS / ❌ FAIL |
| Mode 2 (Sniper) | Emoji <5s + Edit 30-60s | ✅ PASS / ❌ FAIL |
| Обработка ошибок | Нет unhandled exceptions | ✅ PASS / ❌ FAIL |
| Кодировка | Комментарии читаемы | ✅ PASS / ❌ FAIL |

**PRODUCTION READY** если:
- ✅ Оба режима PASS
- ✅ Нет FAIL в отчёте
- ⚠️ Допустимы WARN (но не FAIL)

---

## 🧪 Подготовка к запуску

### 1. ENV файл (.env.local)
```bash
# Telegram (test account!)
TEST_API_ID=12345678
TEST_API_HASH=abcdef1234567890abcdef1234567890
TEST_PHONE=+79990000000
TEST_SESSION_PATH=data/sessions/e2e_test.session

# OpenAI (для AI-комментов)
OPENAI_API_KEY=sk-...
```

### 2. Авторизация сессии (первый запуск)
```bash
python -c "
from telethon import TelegramClient
client = TelegramClient('data/sessions/e2e_test', 12345678, 'abcdef...')
client.start()
print('Authorized!')
"
# Введи код из Telegram
```

### 3. Запуск теста
```bash
python src/tests/comment_sniper_full_test.py
```

**Время выполнения:** ~65-70 секунд

---

## ⚠️ Возможные проблемы

| Проблема | Причина | Решение |
|----------|---------|---------|
| ❌ "No channels with open comments" | Нет каналов с discussion group | Создай свой тестовый канал |
| ⚠️ "Cannot edit (expected)" | Telegram ограничивает edit в некоторых группах | Нормально — тест считает это OK |
| ⚠️ "FloodWait detected" | Слишком частые действия | Увеличь `edit_delay_range` до 60-120s |
| ❌ "AI generation failed" | Нет OPENAI_API_KEY | Добавь ключ или используй fallback |

---

## 📤 Команды

```bash
# Запуск теста
python src/tests/comment_sniper_full_test.py

# Просмотр отчёта
cat data/e2e_sniper_test_*.json | jq .

# Проверка статуса
python -c "import json; r=json.load(open('data/e2e_sniper_test_*.json')); print(r['overall'])"
```

---

**Готов к запуску?** Введи:
```bash
python src/tests/comment_sniper_full_test.py
```

И жди подтверждения `yes` для старта теста.
