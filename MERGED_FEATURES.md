# GRAMGPT — Объединенная Архитектура

## ✅ Что взято из оригинального GRAMGPT

### Core Modules
| Модуль | Функциональность |
|--------|------------------|
| `neuro_modules.py` | NeuroCommenting, NeuroChatting, MassReactionPro (👀→👍→❤️→🔥), NeuroSabotage |
| `human_emulation.py` | DNA (typing speed WPM, error rate, timezone, rhythm), circadian rhythm sync |
| `fingerprint.py` | Device fingerprints, behavioral DNA generation |
| `crisis_manager.py` | AICrisisManager - auto-pause при reports, neutralization strategy |
| `router.py` | MultiChannelRouter (TG, WA, IG, Email, SMS), Unified Inbox |
| `automation.py` | Webhook triggers (Zapier, Make) |

### Bot Handlers
| Handler | Функциональность |
|---------|------------------|
| `commands.py` | /start, /image, /clear, /help, /settings + реферальная система |
| `chat.py` | Текстовые сообщения с human_emulation typing delay |
| `media.py` | Голосовые (transcribe) и фото (vision) |

---

## ✅ Что добавлено нового (превосходит оригинал)

### Advanced Telegram Automation
| Модуль | Функциональность |
|--------|------------------|
| `telegram_user_client.py` | Telethon user API, session persistence, message parsing |
| `comment_sender.py` | 3 стиля комментариев, sentiment analysis, anti-ban delays |
| `account_warmer.py` | Скролл, реакции, подписки, истории с human-паттернами |
| `rate_limiter.py` | Adaptive rate limiting, flood-адаптация |
| `pipeline_orchestrator.py` | Автономный цикл, graceful shutdown, real-time stats |

### Multi-Account & Proxy
| Модуль | Функциональность |
|--------|------------------|
| `account_pool.py` | Пул аккаунтов, round-robin, статусы (active/cooldown/banned) |
| `proxy_manager.py` | HTTP/SOCKS5 прокси, валидация, ротация на ошибках |
| `analytics_exporter.py` | Метрики, risk score, экспорт CSV/JSON |

### Promo Workflow (Уникальная фича, нет у GramGPT)
| Модуль | Функциональность |
|--------|------------------|
| `channel_discovery.py` | Авто-поиск каналов по ключам, фильтр открытых комментов |
| `comment_sniper.py` | Эмодзи первым → отложенная замена на промо |
| `promo_engine.py` | AI-вариации промо + анти-спам защита (0-100 score) |
| `work_modes.py` | 3 режима: 🐢 Reliable / 🚶 Balanced / 🚀 Aggressive |

---

## 🎯 Полная Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                        GRAMGPT Ultimate                      │
├─────────────────────────────────────────────────────────────┤
│  Bot Layer (aiogram)                                         │
│  ├── commands.py (/start, /image, /settings, /help)         │
│  ├── chat.py (текст + human_emulation delays)              │
│  ├── media.py (голос, фото)                                 │
│  ├── admin_pipeline.py (/start_pipeline, /stop, /status)     │
│  └── admin_analytics.py (/add_account, /export, /risk)     │
├─────────────────────────────────────────────────────────────┤
│  Core Engine                                                 │
│  ├── PipelineOrchestrator (главный контроллер)             │
│  ├── WorkModeController (3 режима + auto-downgrade)         │
│  ├── AdaptiveRateLimiter (flood-адаптация)                  │
│  ├── AccountPool (мульти-аккаунт + ротация)                  │
│  └── ProxyManager (HTTP/SOCKS5 + ротация)                   │
├─────────────────────────────────────────────────────────────┤
│  Promo Workflow (Уникально!)                                 │
│  ├── ChannelDiscovery (поиск каналов по ключам)             │
│  ├── CommentSniper (эмодзи → отложенное редактирование)   │
│  └── PromoEngine (AI-генерация + anti-spam)                 │
├─────────────────────────────────────────────────────────────┤
│  Neuro Modules (из оригинала)                               │
│  ├── NeuroCommenting (Thread Hijacking)                     │
│  ├── NeuroChatting (отработка возражений)                   │
│  ├── MassReactionPro (воронка: 👀→👍→❤️→🔥)                 │
│  └── NeuroSabotage (контр-аргументы)                        │
├─────────────────────────────────────────────────────────────┤
│  Human Emulation (из оригинала)                              │
│  ├── DNA: typing speed, error rate, timezone                │
│  ├── Circadian rhythm sync (morning/evening/night)         │
│  └── Organic lifecycle (read, react, story, message)       │
├─────────────────────────────────────────────────────────────┤
│  Safety & Crisis (из оригинала)                              │
│  ├── AICrisisManager (auto-pause при reports)              │
│  ├── FingerprintEngine (device + behavioral DNA)           │
│  └── MultiChannelRouter (TG, WA, IG, Email, SMS)           │
├─────────────────────────────────────────────────────────────┤
│  Data Layer                                                  │
│  ├── SQLite (comment_memory, campaigns, analytics)           │
│  └── JSON (account_pool, exports)                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Уникальные преимущества над GramGPT

| Фича | GramGPT Original | Наша версия |
|------|------------------|-------------|
| **Комментирование** | Только обычные комменты | Sniper: эмодзи → отложенная замена на промо |
| **Поиск каналов** | Ручной выбор | Авто-поиск по ключам + фильтр открытых комментов |
| **Режимы работы** | Нет | 3 режима с авто-даунгрейдом при риске |
| **Прокси** | Нет | HTTP/SOCKS5 с валидацией и ротацией |
| **Мульти-аккаунт** | Нет | Пул с round-robin и статусами |
| **Аналитика** | Мock данные | Real-time + CSV/JSON экспорт + risk score |
| **Telethon** | Нет | Полная поддержка user API |

---

## 📊 Итог

**GRAMGPT Original** был чат-ботом с минимальной автоматизацией (в основном mock/заглушки).

**Наша версия** — полноценная автономная система продвижения:
- ✅ Авто-поиск целевых каналов
- ✅ Стратегия "первый коммент" с отложенным промо
- ✅ 3 режима работы с авто-защитой
- ✅ Мульти-аккаунт с прокси
- ✅ Real-time аналитика
- ✅ Готов к продаже $150-300/мес

**Статус: ГОТОВ К ПРОДАЖЕ**
