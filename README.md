# GRAMGPT

GRAMGPT — ИИ-комбайн для Telegram. Профессиональный бот на Python, [aiogram 3.x](https://docs.aiogram.dev/) и [OpenAI GPT-4o](https://openai.com/). Полноценный опыт взаимодействия с ИИ прямо в Telegram с поддержкой мультимодальности и сохранением истории.

## Основные возможности

### Чат-бот
- **Умный чат**: GPT-4o и GPT-4o-mini для общения на любые темы
- **Постоянная память**: История диалогов в SQLite, контекст сохраняется между сессиями
- **Мультимодальность**:
  - Анализ фото (GPT-4o Vision)
  - Транскрипция голосовых сообщений (Whisper)
- **Генерация изображений**: DALL-E 3 по текстовому описанию (`/image`)
- **Настройки модели**: Выбор модели для каждого пользователя (`/settings`)

### Маркетинг-автоматизация
- **Нейрокомментинг**: AI-генерация осмысленных комментариев под постами
- **Нейрочаттинг**: Автоматические ответы в группах с отработкой возражений
- **Парсинг аудитории**: Сбор и анализ целевой аудитории с поведенческим анализом
- **Прогрев аккаунтов**: Human Emulation Engine — имитация поведения реального пользователя
- **Масс-реакции**: Эмоциональный маппинг и Reaction Funnel
- **Авто-воронки**: Многоэтапные маркетинговые кампании с AI Orchestrator

### Безопасность
- **Anti-Ban Shield**: Предиктивный анализ риска блокировки
- **Device Fingerprinting**: Уникальные отпечатки устройств для каждого аккаунта
- **AI Crisis Manager**: Автоматическое обнаружение и нейтрализация угроз
- **Biological Rhythm Sync**: Имитация циклов активности реального пользователя

### Платформа
- **FastAPI**: REST API для управления кампаниями и аналитикой
- **Mini App**: Telegram Web App для управления через интерфейс
- **TON Connect**: Интеграция оплаты через TON кошелёк
- **Реферальная система**: Приглашение пользователей с бонусами
- **RAG Engine**: Локальная база знаний для контекстных ответов

## Технологический стек

- **Python 3.11+**
- **aiogram 3.x**: Фреймворк для Telegram Bot API
- **OpenAI API**: GPT-4o, DALL-E 3, Whisper
- **FastAPI + Uvicorn**: REST API
- **SQLite**: Локальное хранение данных
- **Pydantic Settings**: Конфигурация через переменные окружения

## Установка и настройка

1. **Клонируйте репозиторий**:
   ```bash
   git clone https://github.com/rpauts2/GRAMGPT.git
   cd GRAMGPT
   ```

2. **Установите зависимости**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Настройте окружение**:
   ```bash
   cp .env.example .env
   # Укажите BOT_TOKEN и OPENAI_API_KEY в файле .env
   ```

4. **Запустите бота**:
   ```bash
   python -m src.app
   ```

## Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Запуск бота и приветствие |
| `/image <описание>` | Генерация изображения (DALL-E 3) |
| `/settings` | Выбор модели ИИ (GPT-4o / GPT-4o-mini) |
| `/clear` | Очистка истории диалога |
| `/help` | Справка по всем командам |

## API Endpoints

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/v1/status` | Статус сервиса |
| POST | `/api/v1/campaigns/create` | Создание маркетинговой кампании |
| GET | `/api/v1/analytics/summary` | Сводка аналитики |
| GET | `/api/v1/marketplace/templates` | Список шаблонов |
| GET | `/panel/` | Mini App (Telegram Web App) |

## Docker

```bash
docker build -t gramgpt .
docker run --env-file .env gramgpt
```

## Структура проекта

```
GRAMGPT/
├── src/
│   ├── app.py                    # Точка входа (API + Bot)
│   ├── config.py                 # Конфигурация
│   ├── api/
│   │   ├── main.py               # FastAPI приложение
│   │   ├── web3.py               # TON Connect endpoints
│   │   └── static/mini-app/      # Telegram Mini App
│   ├── core/
│   │   ├── openai_client.py      # OpenAI API клиент
│   │   ├── human_emulation.py    # Human Emulation Engine
│   │   ├── neuro_modules.py      # Нейрокомментинг, нейрочаттинг
│   │   ├── orchestrator.py       # AI Orchestrator
│   │   ├── account_manager.py    # Управление аккаунтами
│   │   ├── fingerprint.py        # Device Fingerprinting
│   │   ├── crisis_manager.py     # AI Crisis Manager
│   │   ├── autofunnel.py         # Авто-воронки
│   │   ├── router.py             # Multi-Channel Router
│   │   ├── referral.py           # Реферальная система
│   │   ├── avatar.py             # AI Video Avatars
│   │   ├── rag/engine.py         # RAG Engine
│   │   └── voice/cloning.py      # Voice Cloning
│   ├── db/
│   │   ├── database.py           # SQLite база данных
│   │   └── memory.py             # Память диалогов
│   ├── services/
│   │   ├── parser.py             # Поведенческий анализ
│   │   ├── hyper_parser.py       # Cross-platform парсинг
│   │   └── bot/
│   │       ├── main.py           # Инициализация бота
│   │       ├── handlers/         # Обработчики команд
│   │       └── middlewares/      # Middleware (логирование)
│   └── utils/
│       └── i18n.py               # Интернационализация
├── tests/                        # Тесты
├── requirements.txt
├── Dockerfile
└── .env.example
```
