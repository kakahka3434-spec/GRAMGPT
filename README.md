# 🚀 GRAMGPT ULTIMATE

**Production-Ready Telegram AI Automation SaaS** — превосходя gramgpt.io по всем параметрам.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

---

## 🔥 КЛЮЧЕВЫЕ ПРЕИМУЩЕСТВА

| Фича | GramGPT.io | GRAMGPT Ultimate |
|------|------------|------------------|
| **AI Models** | GPT-3.5/4 (paid) | OpenAI + OpenRouter FREE + Groq FREE |
| **Sniper Mode** | ❌ | ✅ Эмодзи → edit → промо |
| **Context Awareness** | ❌ | ✅ RAG + Few-shot learning |
| **Anti-Ban** | Basic limits | ✅ ML Predictor + Auto-downgrade |
| **Multi-channel** | Telegram only | ✅ WA/IG/Email ready |
| **Tone Matching** | ❌ | ✅ Адаптация под стиль чата |
| **Multi-language** | EN only | ✅ 8 языков (RU, EN, ES, DE, FR, IT, PT, UK) |
| **Free Tier** | Trial only | ✅ Permanent free tier |

---

## 🎯 ВОЗМОЖНОСТИ

### 🔹 CommentSniper
- **Direct Mode**: AI-комментарий с контекстом поста (RAG: последние 10 постов канала)
- **Sniper Mode**: эмодзи → задержка (настраиваемая) → edit на промо-текст
- **A/B тестирование**: 2-3 варианта текста → авто-выбор победителя по вовлечённости

### 🔹 ChannelDiscovery
- Поиск по ключевым словам + фильтрация: открытые комменты, язык, активность
- Кэширование результатов (7 дней TTL) + инвалидация при изменении канала
- Экспорт найденных каналов в CSV/JSON

### 🔹 HumanEmulation + Anti-Ban Shield
- **DNA профиля**: WPM (40-120), error_rate (0.5-3%), circadian rhythm
- **Fingerprint**: device, UA, screen, OS — ротация при долгой сессии
- **Predictive Ban Score**: ML-модель оценивает риск перед действием

### 🔹 MultiChannelRouter
- Telegram → WhatsApp (Twilio) → Instagram (instagrapi) → Email (SMTP)
- Unified Inbox: все сообщения в одном интерфейсе
- Синхронизация статуса: «отправлено», «прочитано», «ответил»

---

## 🏗️ АРХИТЕКТУРА

```
┌─────────────────────────────────────────────────────┐
│                  Traefik (Reverse Proxy)            │
│                  SSL Termination + Rate Limiting    │
└─────────────────────────────────────────────────────┘
                         │
        ┌────────────────┴────────────────┐
        │                                 │
┌───────▼────────┐              ┌────────▼────────┐
│   FastAPI API  │              │  Celery Worker  │
│   (4 workers)  │              │  (4 concurrency)│
└───────┬────────┘              └────────┬────────┘
        │                                 │
        └────────────────┬────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
┌───────▼────────┐ ┌─────▼──────┐ ┌──────▼──────┐
│   PostgreSQL   │ │   Redis    │ │ Prometheus  │
│   (Database)   │ │ (Cache+MQ) │ │  (Metrics)  │
└────────────────┘ └────────────┘ └─────────────┘
```

---

## 🚀 БЫСТРЫЙ СТАРТ

### 1. Клонирование

```bash
git clone https://github.com/yourusername/gramgpt-ultimate.git
cd gramgpt-ultimate
```

### 2. Настройка окружения

```bash
cp .env.prod.example .env.prod
nano .env.prod  # Заполните все значения
```

### 3. Генерация ключей безопасности

```bash
# JWT Secret
openssl rand -hex 32

# Fernet Encryption Key
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 4. Запуск через Docker

```bash
docker-compose -f docker-compose.prod.yml up --build -d
```

### 5. Проверка

```bash
# Статус сервисов
docker-compose -f docker-compose.prod.yml ps

# Логи
docker-compose -f docker-compose.prod.yml logs -f api

# API Docs
curl https://yourdomain.com/docs
```

---

## 📁 СТРУКТУРА ПРОЕКТА

```
gramgpt-ultimate/
├── src/
│   ├── api/              # FastAPI endpoints & routes
│   │   ├── main.py
│   │   ├── config.py
│   │   └── routes/
│   │       ├── miniapp.py
│   │       ├── payments.py
│   │       └── ...
│   ├── core/             # Business logic
│   │   ├── comment_sniper.py
│   │   ├── promo_engine.py
│   │   ├── flood_predictor.py
│   │   ├── tone_matcher.py
│   │   ├── i18n_manager.py
│   │   └── ...
│   ├── db/               # Database models & migrations
│   │   ├── database.py
│   │   ├── models.py
│   │   └── alembic/
│   ├── tests/            # Unit & E2E tests
│   └── utils/            # Helpers
├── static/               # Mini App frontend
│   └── index.html
├── monitoring/           # Prometheus config
├── docker-compose.prod.yml
├── Dockerfile
├── requirements.txt
├── .env.prod.example
├── DEPLOYMENT.md
└── README.md
```

---

## 🧪 ТЕСТИРОВАНИЕ

### Запуск всех тестов

```bash
pytest src/tests -v --cov=src
```

### E2E тест CommentSniper

```bash
python -m src.tests.comment_sniper_full_test
```

### Проверка кода

```bash
flake8 src --max-line-length=127
black --check src
mypy src --ignore-missing-imports
```

---

## 📊 МОНТОРИНГ

### Prometheus Metrics

Доступны по адресу: `http://localhost:9090`

Ключевые метрики:
- `http_requests_total` — всего запросов к API
- `http_request_duration_seconds` — время ответа
- `celery_tasks_pending` — длина очереди задач
- `db_connections_active` — активные подключения к БД

### Grafana Dashboard

```bash
docker run -d --name grafana \
  -p 3000:3000 \
  -v grafana_data:/var/lib/grafana \
  grafana/grafana:latest
```

---

## 💼 ТАРИФЫ (SaaS модель)

| Тариф | Цена | Аккаунты | Комментарии/день | Фичи |
|-------|------|----------|------------------|------|
| **Free** | $0 | 1 | 10 | Direct mode, базовый AI |
| **Pro** | $49/мес | 5 | 500 | Sniper mode, RAG, Tone matching |
| **Agency** | $149/мес | 20 | 2000 | Все фичи + API доступ |
| **Enterprise** | $299/мес | Unlimited | Unlimited | White-label, приоритетная поддержка |

---

## 🔐 БЕЗОПАСНОСТЬ

- **JWT аутентификация** + Refresh tokens
- **RBAC**: user / admin / superadmin роли
- **Шифрование** чувствительных данных (AES-256)
- **Rate limiting** на пользователя и эндпоинт
- **Аудит-лог** всех критических действий
- **GDPR compliance**: экспорт и удаление данных по запросу

---

## 📖 ДОКУМЕНТАЦИЯ

- [DEPLOYMENT.md](./DEPLOYMENT.md) — полное руководство по развертыванию
- [API Docs](https://yourdomain.com/docs) — Swagger UI (OpenAPI)
- [STRATEGIC_PLAN.md](./STRATEGIC_PLAN.md) — стратегия развития
- [PROMPTS_GUIDE.md](./PROMPTS_GUIDE.md) — коллекция AI промптов

---

## 🤝 CONTRIBUTING

1. Fork the repo
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📞 ПОДДЕРЖКА

- **Email**: support@gramgpt.io
- **Telegram**: [@gramgpt_support](https://t.me/gramgpt_support)
- **Documentation**: https://docs.gramgpt.io

---

## 📜 ЛИЦЕНЗИЯ

MIT License — см. [LICENSE](./LICENSE) файл.

---

## 🎯 ROADMAP

### Q1 2025
- [x] Production Docker setup
- [x] CI/CD pipeline
- [x] Monitoring & alerting
- [ ] Payment integration (Stripe + Crypto)
- [ ] Multi-tenancy support

### Q2 2025
- [ ] WhatsApp integration
- [ ] Instagram integration
- [ ] Voice comments (TTS)
- [ ] Avatar generation for accounts

---

**Made with ❤️ by GRAMGPT Team**

*Превосходя возможности конкурентов, создаем будущее автоматизации.*
