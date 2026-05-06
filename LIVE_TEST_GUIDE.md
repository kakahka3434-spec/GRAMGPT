# 🔴 CommentSniper Live Test Guide

## 📋 Подготовка к тесту (5 минут)

### Шаг 1: Создай тестовый канал
1. Открой Telegram
2. Создай новый канал: "GRAMGPT Test Channel"
3. **Обязательно** включи Discussion Group:
   - Настройки канала → Discussion → Enable discussion
   - Создай или выбери группу для комментариев

### Шаг 2: Добавь аккаунт в админы
1. Добавь тестовый аккаунт (тот, что в TEST_PHONE) в администраторы канала
2. Дай права: Post messages + Edit messages

### Шаг 3: Настрой окружение
Создай `.env.local`:
```bash
# Telegram credentials (test account)
TEST_API_ID=12345678
TEST_API_HASH=abcdef1234567890abcdef1234567890
TEST_PHONE=+79990000000

# Test channel (без @)
TEST_CHANNEL=my_test_channel_2024

# Session file
TEST_SESSION_PATH=data/sessions/test_live.session
```

### Шаг 4: Авторизуй сессию (если новая)
```bash
python -c "
from telethon import TelegramClient
client = TelegramClient('data/sessions/test_live', 12345678, 'abcdef1234567890abcdef1234567890')
client.start()
print('Authorized!')
"
# Введи код из Telegram
```

---

## 🚀 Запуск теста

```bash
python src/tests/comment_sniper_live.py
```

**Подтверди канал** когда спросит:
```
⚠️  Confirm test channel @my_test_channel_2024? (yes/no): yes
```

---

## 📊 Что произойдёт

1. **T+0s** — Скрипт подключится к Telegram
2. **T+2s** — Запустит CommentSniper на мониторинг канала
3. **T+5s** — Опубликует тестовый пост
4. **T+5-10s** — Отправит эмодзи-комментарий (👍 или 🔥)
5. **T+35-65s** — Отредактирует комментарий на промо-текст
6. **T+70s** — Остановит мониторинг и выведет отчёт

**Весь тест занимает ~70 секунд.**

---

## ✅ Ожидаемый результат

```
[14:32:10.123 | T+2.1s] ✅ [OK] Emoji comment sent
   Details: Delay: 2.3s (target: <5s)
   
[14:32:45.456 | T+37.4s] ✅ [OK] Edit completed
   Details: Total delay: 37.4s
```

Итог:
```
🎉 CommentSniper: PRODUCTION READY
```

---

## ⚠️ Возможные проблемы и решения

### ❌ "Failed to connect to Telegram"
**Причина:** Неправильные API_ID/API_HASH или нет интернета  
**Решение:** Проверь `.env.local`, запусти `python -c "from telethon..."`

### ❌ "Cannot access test channel"
**Причина:** Аккаунт не в админах канала  
**Решение:** Добавь аккаунт в админы, проверь username канала

### ❌ "Emoji comment not detected"
**Причина:**
- В канале нет discussion group
- У аккаунта нет прав на комментирование
- Комментарии закрыты

**Решение:**
1. Проверь: Settings → Discussion → Enabled
2. Проверь: Members → Права аккаунта

### ❌ "Edit not completed"
**Причина:**
- Telegram не даёт редактировать сообщения в discussion group
- FloodWaitError (редко на тестовом аккаунте)

**Решение:**
- Попробуй другой канал (создай новый)
- Увеличь задержки в `WorkModeController` до 60-120s

### ⚠️ "Emoji delay too high"
**Причина:** Медленное соединение или загруженный аккаунт  
**Нормально:** До 5 секунд приемлемо для теста

---

## 🧪 Ручная проверка (если скрипт не работает)

Если скрипт падает — проверь вручную:

```python
from telethon import TelegramClient

client = TelegramClient('test', API_ID, 'API_HASH')
client.start()

# 1. Проверь доступ к каналу
channel = await client.get_entity('my_test_channel')
print(f"OK: {channel.title}")

# 2. Проверь discussion group
from telethon.tl.functions.channels import GetFullChannelRequest
full = await client(GetFullChannelRequest(channel))
print(f"Discussion ID: {full.full_chat.linked_chat_id}")

# 3. Отправь комментарий
msg = await client.send_message(channel, "Test post")
print(f"Post ID: {msg.id}")

# 4. Проверь комментирование
discussion = await client.get_entity(full.full_chat.linked_chat_id)
comment = await client.send_message(discussion, "👍", reply_to=msg.id)
print(f"Comment sent: {comment.id}")

# 5. Попробуй отредактировать
await client.edit_message(discussion, comment.id, "Edited promo text")
print("Edit successful!")
```

---

## 📝 Логирование результатов

После теста создаётся JSON-отчёт:
```
data/sniper_live_test_20250115_143210.json
```

Структура:
```json
{
  "total_tests": 15,
  "passed": 13,
  "failed": 0,
  "warnings": 2,
  "duration_sec": 67.3,
  "results": [...]
}
```

---

## 🎯 Критерии PRODUCTION READY

| Критерий | Минимум | Целевой |
|----------|---------|---------|
| Подключение к Telegram | < 10s | < 5s |
| Отправка эмодзи | < 5s | < 3s |
| Редактирование | 180-300s | 180-300s |
| Ошибки | 0 | 0 |
| Предупреждения | ≤ 2 | 0 |

**PRODUCTION READY** если:
- ✅ Все основные тесты passed
- ✅ Нет critical failures
- ⚠️ Допустимы minor warnings

---

## 🚀 После успешного теста

1. **Обнови статус в AUDIT_REPORT.md:**
   ```
   CommentSniper: REAL → PRODUCTION READY
   ```

2. **Добавь в README:**
   ```
   ## Live Tests ✅
   - CommentSniper: Passed on 2025-01-15
   ```

3. **Можно запускать для клиентов!**

---

## 🆘 Если тест упал

1. **Сохрани лог:**
   ```bash
   python src/tests/comment_sniper_live.py 2>&1 | tee sniper_test.log
   ```

2. **Проверь JSON-отчёт:**
   ```bash
   cat data/sniper_live_test_*.json
   ```

3. **Кинь мне:**
   - Лог теста
   - JSON отчёт
   - Скриншот настроек канала (если проблема с доступом)

---

**Готов к запуску?** 

```bash
python src/tests/comment_sniper_live.py
```

💪 Удачи! 
