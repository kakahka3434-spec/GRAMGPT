# GRAMGPT Ultimate — Telegram Promotion System

**Автономная система продвижения в Telegram с AI-генерацией контента, мульти-аккаунтом и стратегией "первый коммент".**

## 🚀 Быстрый старт

```bash
# 1. Установка зависимостей
pip install -r requirements.txt

# 2. Настройка окружения
copy .env.example .env.local
# Отредактируй .env.local (API ключи, Telegram credentials)

# 3. Первая авторизация (Telethon)
python -c "
from src.services.telegram_user_client import TelegramUserClient
client = TelegramUserClient(api_id=..., api_hash='...', phone='+...')
client.connect()  # Введите код из Telegram
"

# 4. Запуск бота
python -m src.services.bot.main

# 5. Или запуск теста
python tests/test_promo_workflow.py
```

---

## ✨ Ключевые фичи

### 1. 🎯 Comment Sniper (Уникально!)
**Стратегия, которой нет у конкурентов:**
- Мгновенный эмодзи-коммент при новом посте (1-3 сек)
- Отложенное редактирование в промо-текст (3-10 мин)
- Обход гонки за первый коммент

### 2. 🔍 Channel Discovery
- Авто-поиск каналов по ключевым словам
- Фильтр каналов с открытыми комментариями
- Кэширование результатов

### 3. 🎮 3 Режима работы
| Режим | Комментов/день | Риск | Когда использовать |
|-------|---------------|------|------------------|
| 🐢 Reliable | 5-10 | Низкий | Дорогие аккаунты |
| 🚶 Balanced | 15-30 | Средний | Стандарт |
| 🚀 Aggressive | 40-80 | Высокий | Максимум |

**Авто-даунгрейд:** При обнаружении риска режим автоматически понижается.

### 4. 👥 Multi-Account + Proxy
- Пул аккаунтов с round-robin ротацией
- HTTP/SOCKS5 прокси с валидацией
- Авто-ротация прокси при ошибках
- Статусы: active/cooldown/banned/warming

### 5. 🧠 Neuro Modules (из оригинала)
- **NeuroCommenting** — Thread Hijacking
- **NeuroChatting** — Отработка возражений
- **MassReactionPro** — Воронка реакций 👀→👍→❤️→🔥
- **NeuroSabotage** — Контр-аргументы

### 6. 🛡️ Anti-Ban Protection
- **Human Emulation** — DNA (typing speed, error rate, timezone)
- **Fingerprint** — Device + behavioral fingerprints
- **Crisis Manager** — Auto-pause при reports
- **Adaptive Rate Limiter** — Динамические задержки

---

## 📁 Структура проекта

```
GRAMGPT/
├── src/
│   ├── api/                  # FastAPI endpoints
│   ├── core/
│   │   ├── neuro_modules.py  # AI комментинг/чаттинг
│   │   ├── human_emulation.py # Human-like behavior
│   │   ├── fingerprint.py    # Device fingerprints
│   │   ├── crisis_manager.py # Crisis detection
│   │   ├── router.py         # Multi-channel routing
│   │   ├── rate_limiter.py   # Adaptive limiting
│   │   ├── work_modes.py     # 3 режима работы
│   │   ├── account_pool.py   # Multi-account
│   │   ├── proxy_manager.py  # Proxy rotation
│   │   └── pipeline_orchestrator.py # Main controller
│   ├── services/
│   │   ├── telegram_user_client.py  # Telethon
│   │   ├── comment_sender.py        # Комменты
│   │   ├── account_warmer.py        # Прогрев
│   │   ├── channel_discovery.py     # Поиск каналов
│   │   ├── comment_sniper.py        # Sniper
│   │   ├── promo_engine.py          # Промо
│   │   ├── parser.py                # Smart parser
│   │   └── bot/
│   │       ├── handlers/
│   │       │   ├── commands.py      # /start, /help
│   │       │   ├── chat.py         # Текст
│   │       │   ├── media.py         # Голос/фото
│   │       │   ├── admin_pipeline.py # Pipeline cmd
│   │       │   └── admin_analytics.py # Analytics cmd
│   │       └── main.py
│   ├── db/
│   │   ├── database.py
│   │   ├── memory.py
│   │   └── comment_memory.py
│   └── config.py
├── tests/
│   ├── test_promo_workflow.py
│   ├── test_multi_account_analytics.py
│   └── test_pipeline_advanced.py
├── data/
│   └── sessions/             # Telethon sessions
├── exports/                  # CSV/JSON экспорты
├── requirements.txt
├── .env.local
└── README.md
```

---

## 🎛️ Команды бота

### Основные
```
/start — Запуск бота
/help — Справка
/image <описание> — DALL-E 3
/clear — Очистить историю
/settings — Выбор модели
```

### Pipeline
```
/start_pipeline <каналы> <стиль> <режим>
/stop_pipeline
/status
/mode <reliable|balanced|aggressive>
/sniper_start <каналы> <ссылка>
```

### Multi-Account
```
/add_account <phone> <session> [proxy]
/remove_account <phone>
/list_accounts
/mark_cooldown <phone> <minutes>
```

### Аналитика
```
/analytics [hours]
/export_stats [hours] [csv|json]
/risk_report
```

---

## 💰 Монетизация

### Тарифы для клиентов
| План | Цена | Что входит |
|------|------|-----------|
| **Starter** | $150/мес | 1 аккаунт, 10-20 комментов/день, reliable mode |
| **Pro** | $300/мес | 3 аккаунта, 30-60 комментов/день, все режимы |
| **Agency** | $500/мес | 10 аккаунтов, white-label, API доступ |

### Дополнительные услуги
- Настройка под ключ: +$200
- Обучение команды: +$100/час
- Приоритетная поддержка: +$50/мес

---

## 🔧 Технические требования

### Минимальные
- Python 3.10+
- 1GB RAM
- 1 аккаунт Telegram

### Рекомендуемые
- Python 3.11+
- 2GB RAM
- 3-5 аккаунтов Telegram
- Прокси (1 на аккаунт)

---

## 📊 Сравнение с конкурентами

| Фича | GramGPT Original | Комментаторы | Наша версия |
|------|------------------|--------------|-------------|
| Comment Sniper | ❌ | ❌ | ✅ Уникально |
| Channel Discovery | ❌ | ⚠️ Ручной | ✅ Авто |
| Multi-Account | ❌ | ⚠️ Дорого | ✅ Встроено |
| Work Modes | ❌ | ❌ | ✅ 3 режима |
| Proxy Rotation | ❌ | ⚠️ Ручная | ✅ Авто |
| Analytics | ❌ Mock | ⚠️ Базовая | ✅ Full |
| Human Emulation | ⚠️ Частично | ❌ | ✅ DNA |
| Crisis Manager | ⚠️ Заглушка | ❌ | ✅ AI |
| Neuro Modules | ✅ | ❌ | ✅ |
| Telethon Support | ❌ | ❌ | ✅ Full |

---

## 🛡️ Безопасность

### Защита от банов
- ✅ Circadian rhythm sync (активность по часам)
- ✅ DNA-based typing speed (WPM: 120-200)
- ✅ Random error injection (1-5%)
- ✅ Device fingerprint rotation
- ✅ Adaptive delays (flood-адаптация)
- ✅ Auto-pause при reports

### Рекомендации
- Начинайте с режима `reliable`
- Используйте прокси (1 на аккаунт)
- Не превышайте лимиты режима
- Мониторьте `/risk_report`

---

## 📈 Метрики и KPI

### Внутренние
- Comments/hour
- Success rate (%)
- Risk score (0-100)
- Flood errors count
- Active/cooldown/banned ratio

### Внешние (для клиента)
- Упоминаний бренда
- Переходов по ссылкам
- Новых подписчиков
- ROI кампании

---

## 🔗 API

### Endpoints
```
GET  /api/v1/status           — Статус системы
POST /api/v1/campaigns/create — Создать кампанию
GET  /api/v1/analytics/summary — Аналитика
GET  /api/v1/marketplace/templates — Шаблоны
```

### Mini App
- URL: `https://t.me/your_bot/panel`
- Функциональность: управление кампаниями, аналитика

---

## 📞 Поддержка

### Каналы
- Telegram: @gramgpt_support
- Email: support@gramgpt.io

### Документация
- `COMMANDS.md` — Полный список команд
- `MERGED_FEATURES.md` — Объединенная архитектура
- `tests/` — Примеры использования

---

## 📄 Лицензия

Private use only. Commercial license available upon request.

---

## 🎉 Итог

**GRAMGPT Ultimate** — это не просто комментатор, а полноценная система автономного продвижения в Telegram:

- ✅ Авто-поиск целевых каналов
- ✅ Уникальная стратегия "первый коммент"
- ✅ 3 режима работы с авто-защитой
- ✅ Мульти-аккаунт с прокси
- ✅ Real-time аналитика
- ✅ Готов к продаже $150-300/мес

**Готов к запуску! 🚀**
