# 🚀 GRAMGPT — Telegram Auto-Marketing Platform

**AI-powered automation for Telegram promotion, commenting, and engagement**

---

## 🎯 Что такое GRAMGPT?

GRAMGPT — это полностью автоматизированная система для:
- ✅ **Авто-комментирования** в целевых каналах (стратегия "первый коммент")
- ✅ **AI-генерации** персонализированных комментариев  
- ✅ **Умного парсинга** популярных постов по нишам
- ✅ **Мульти-аккаунтного** управления с ротацией
- ✅ **Защиты от банов** (anti-ban, human emulation, crisis detection)
- ✅ **Аналитики** и отчётов в реальном времени

---

## 🚀 Быстрый старт (3 клика)

### 1️⃣ Установка
```bash
git clone https://github.com/kakahka3434-spec/GRAMGPT.git
cd GRAMGPT
pip install -r requirements.txt
```

### 2️⃣ Конфигурация
```bash
# Скопируй и отредактируй .env
cp .env.example .env.local

# Заполни:
# - TELEGRAM_API_ID (из https://my.telegram.org)
# - TELEGRAM_API_HASH
# - OPENROUTER_API_KEY (бесплатный ключ OpenRouter)
# - Другие параметры
```

### 3️⃣ Запуск
```bash
# Terminal 1: API Server
uvicorn src.api.main:app --reload --port 8000

# Terminal 2: Оставить открытым
# API будет доступен на http://127.0.0.1:8000
```

**Готово! ✅**

---

## 📊 Дашборд & API

### Web Interface
```
http://127.0.0.1:8000/
```

Видишь:
- 📈 Real-time статистику комментариев
- 🎯 Активные кампании
- 💰 Аналитику вовлечённости
- ⚙️ Управление аккаунтами

### API Endpoints (для интеграций)

#### Получить статус
```bash
curl http://127.0.0.1:8000/api/v1/status
# → {"status": "GRAMGPT Engine Online"}
```

#### Создать кампанию
```bash
curl -X POST http://127.0.0.1:8000/api/v1/campaigns/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Crypto Promo",
    "goal": "engagement"
  }'
```

#### Получить аккаунты
```bash
curl http://127.0.0.1:8000/api/v1/accounts
```

#### Дашборд
```bash
curl http://127.0.0.1:8000/api/v1/dashboard
```

---

## 💡 Ключевые фичи

### 🐢 3 Режима работы

| Режим | Комментов/день | Риск | Лучше всего для |
|-------|---|---|---|
| **Reliable** 🐢 | 5-10 | 🟢 Низкий | Новые аккаунты, дорогие |
| **Balanced** 🚶 | 15-30 | 🟡 Средний | Стандартные кампании |
| **Aggressive** 🚀 | 40-80 | 🔴 Высокий | Максимальный охват |

### 🎯 Comment Sniper (Уникально!)
1. Ловит новый пост в канале (1-3 сек)
2. Отправляет быстрый эмодзи-коммент
3. Через 3-10 минут редактирует в промо-текст
4. **Результат:** Высокая видимость + органично выглядит

### 🤖 AI-генерация комментариев
- Анализирует пост (тему, тон, аудиторию)
- Генерирует релевантный комментарий
- Адаптируется к языку поста
- Избегает спама-паттернов

### 👥 Мульти-аккаунт + Прокси
- Управляй 5, 10, 100+ аккаунтами
- Автоматическая ротация
- HTTP/SOCKS5 прокси поддержка
- Статусы: active / cooldown / banned / warming

### 🛡️ Anti-Ban Protection
- **Human Emulation** — имитация человеческого поведения
- **Fingerprint** — уникальные "отпечатки" устройства
- **Crisis Manager** — обнаруживает и останавливает риски
- **Adaptive Rate Limiter** — динамические задержки

### 📈 Analytics & Reports
- Real-time статистика
- Экспорт в PDF/CSV
- Тепловые карты активности
- ROI калькулятор

---

## 🔧 Примеры использования

### Пример 1: Запустить комментирование по нишам

```python
from src.core.pipeline_orchestrator import PipelineOrchestrator

async def run_crypto_promo():
    orchestrator = PipelineOrchestrator()
    
    # Создать стратегию
    strategy = await orchestrator.create_campaign_strategy(
        name="Crypto Explosion",
        goal="engagement",
        niches=["crypto", "blockchain", "defi"],
        work_mode="balanced"  # 🚶
    )
    
    # Запустить
    await orchestrator.execute_strategy(strategy)
    
    # Мониторить
    stats = await orchestrator.get_campaign_stats("Crypto Explosion")
    print(stats)

# Запустить
import asyncio
asyncio.run(run_crypto_promo())
```

### Пример 2: Управление аккаунтами

```python
from src.core.account_pool import AccountPool

pool = AccountPool()

# Добавить аккаунт
await pool.add_account(
    phone="+79990000000",
    api_id=12345678,
    api_hash="abc...",
    session_file="sessions/account1.session"
)

# Получить активные
active = await pool.get_active_accounts()
print(f"Active accounts: {len(active)}")

# Проверить статус
status = await pool.get_account_status(account_id="acc_001")
print(status)  # → {"status": "active", "risk_score": 0.2}
```

### Пример 3: Channel Discovery

```python
from src.services.channel_discovery import ChannelDiscovery

discovery = ChannelDiscovery()

# Найти каналы по ключевым словам
channels = await discovery.discover_channels(
    keywords=["python", "programming", "dev"],
    min_subscribers=10000,
    has_comments=True,
    language="en"
)

print(f"Found {len(channels)} channels")
for ch in channels[:5]:
    print(f"- {ch.title} ({ch.subscribers} subscribers)")
```

---

## 📋 Файловая структура

```
GRAMGPT/
├── src/
│   ├── api/
│   │   ├── main.py              # FastAPI app
│   │   ├── static/
│   │   │   ├── landing/         # Landing page
│   │   │   └── mini-app/        # Dashboard UI
│   │   └── web3.py              # Web3 integration
│   ├── core/
│   │   ├── account_pool.py      # Multi-account
│   │   ├── proxy_manager.py     # Proxy rotation
│   │   ├── rate_limiter.py      # Rate limiting
│   │   ├── work_modes.py        # 3 режима
│   │   ├── crisis_manager.py    # Crisis detection
│   │   ├── human_emulation.py   # Human behavior
│   │   ├── fingerprint.py       # Device FP
│   │   ├── neuro_modules.py     # AI commenting
│   │   └── pipeline_orchestrator.py  # Main controller
│   ├── services/
│   │   ├── telegram_user_client.py
│   │   ├── comment_sender.py
│   │   ├── comment_sniper.py
│   │   ├── channel_discovery.py
│   │   ├── account_warmer.py
│   │   ├── promo_engine.py
│   │   └── parser.py
│   ├── db/
│   │   ├── database.py
│   │   ├── memory.py
│   │   └── comment_memory.py
│   ├── utils/
│   └── config.py
├── data/
│   └── gramgpt.db               # SQLite database
├── .env.local                   # Your secrets
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## ⚙️ Конфигурация (.env.local)

```ini
# Telegram Bot API
BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11

# Telegram User API (from https://my.telegram.org)
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=abcdef1234567890abcdef1234567890
TELEGRAM_PHONE=+79990000000

# AI Provider
AI_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-xxxx...
OPENAI_API_KEY=sk-...          # Optional
GROQ_API_KEY=gsk-...            # Optional

# Model settings
MODEL_NAME=mistralai/mistral-7b-instruct:free
TEMPERATURE=0.7
MAX_TOKENS=2000

# Database
DATABASE_URL=sqlite:///./data/gramgpt.db
# Or PostgreSQL:
# DATABASE_URL=postgresql://user:pass@localhost/gramgpt

# Server
API_PORT=8000
API_HOST=127.0.0.1

# Rate limiting
RATE_LIMIT_ENABLED=true
MAX_COMMENTS_PER_HOUR=100

# Debug
DEBUG=false
LOG_LEVEL=INFO
```

---

## 🧪 Тестирование

### Запустить тесты
```bash
pytest tests/ -v
```

### Тест конкретного модуля
```bash
pytest tests/test_comment_sniper.py -v
```

### С покрытием
```bash
pytest --cov=src tests/
```

---

## 🚀 Deployment

### Docker
```bash
docker build -t gramgpt .
docker run -p 8000:8000 --env-file .env.local gramgpt
```

### SystemD (Linux)
```bash
# /etc/systemd/system/gramgpt.service
[Unit]
Description=GRAMGPT API Server
After=network.target

[Service]
Type=simple
User=gramgpt
WorkingDirectory=/opt/gramgpt
Environment="PATH=/opt/gramgpt/venv/bin"
ExecStart=/opt/gramgpt/venv/bin/python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000

[Install]
WantedBy=multi-user.target
```

启動:
```bash
sudo systemctl start gramgpt
sudo systemctl enable gramgpt
sudo systemctl status gramgpt
```

---

## 🤝 Поддержка & Документация

- 📖 **Полная документация:** [docs.gramgpt.io](https://docs.gramgpt.io)
- 💬 **Telegram чат:** [@gramgpt_support](https://t.me/gramgpt_support)
- 📧 **Email:** support@gramgpt.io
- 🐛 **Баги:** [GitHub Issues](https://github.com/kakahka3434-spec/GRAMGPT/issues)

---

## 📜 License

MIT License — используй свободно для коммерческих и личных проектов.

---

## ⚠️ Дисклеймер

GRAMGPT предоставляется "as-is". Ты ответственен за:
- Соблюдение Telegram Terms of Service
- Соблюдение законов о маркетинге в твоей стране
- Ответственное использование (не спам)

Авторы не несут ответственности за банны, штрафы или другие последствия неправомерного использования.

---

**🎉 Готов к запуску? Начни с Быстрого старта выше!**

*Последнее обновление: 2026-05-06*
