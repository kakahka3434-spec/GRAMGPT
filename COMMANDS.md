# GRAMGPT — Полный список команд

## 🤖 Основные команды (Bot)

### Общие
```
/start — Запуск бота, приветствие, реферальная ссылка
/help — Справка по всем командам
/settings — Выбор модели ИИ (GPT-4o / GPT-4o-mini)
/clear — Очистить историю диалога
```

### Медиа
```
/image <описание> — Генерация изображения (DALL-E 3)
[голосовое] — Распознавание речи и ответ
[фото] — Анализ изображения
```

---

## 🎯 Pipeline управление

```
/start_pipeline <каналы> <стиль> <режим> — Запуск автоматизации
/stop_pipeline — Остановка (graceful)
/status — Статус пайплайна
/sniper_start <каналы> <ссылка> — Запуск Comment Sniper
/mode <reliable|balanced|aggressive> — Смена режима работы
```

**Примеры:**
```
/start_pipeline durov,cryptonews engaging balanced
/sniper_start durov,cryptonews https://t.me/mybot
/mode aggressive
```

---

## 👥 Multi-Account управление

```
/add_account <phone> <session> [proxy] — Добавить аккаунт
/remove_account <phone> — Удалить аккаунт
/list_accounts — Список аккаунтов со статусами
/mark_cooldown <phone> <minutes> — Ручной cooldown
```

**Примеры:**
```
/add_account +79158443612 data/sessions/account2.session socks5://proxy:1080
/add_account +79158443613 data/sessions/account3.session
```

---

## 📊 Аналитика

```
/analytics [hours] — Быстрая сводка
/export_stats [hours] [csv|json] — Экспорт данных
/risk_report — Риск-отчёт с рекомендациями
/export_csv 24 — CSV за 24 часа
/export_json 7 — JSON за 7 дней
```

---

## 🧼 Прогрев аккаунтов

```
/quick_warmup — Быстрый прогрев (15 мин)
/set_warmup_interval <hours> — Интервал прогрева
/warmup_status — Статус прогрева
```

---

## 🔍 Channel Discovery

```
/discover <ключевые слова> [min_members] — Поиск каналов
/filter_channels — Фильтр с открытыми комментами
/add_target <username> — Добавить канал вручную
```

**Пример:**
```
/discover crypto,trading,nft 5000
```

---

## 🛡️ Safety & Crisis

```
/pause_all — Пауза всех аккаунтов
/resume_all — Возобновить
/crisis_status — Проверка на кризис
```

---

## 📋 Полный пример запуска

```
# 1. Добавляем аккаунты
/add_account +79990000001 data/sessions/acc1.session socks5://p1:1080
/add_account +79990000002 data/sessions/acc2.session socks5://p2:1080

# 2. Проверяем статус
/list_accounts

# 3. Ищем каналы (или указываем вручную)
/discover crypto,trading 1000

# 4. Запускаем в обычном режиме
/start_pipeline durov,cryptonews,whale engaging balanced

# Или в режиме Sniper (эмодзи → промо)
/sniper_start durov,cryptonews https://t.me/mybot

# 5. Мониторим
/status
/analytics

# 6. Экспортируем отчёт
/export_stats 24 csv
/risk_report

# 7. Останавливаем
/stop_pipeline
```

---

## 🎮 Режимы работы

| Режим | Комментов/день | Задержки | Риск | Когда использовать |
|-------|---------------|----------|------|------------------|
| 🐢 **reliable** | 5-10 | 3-10 мин | Низкий | Дорогие аккаунты, осторожность |
| 🚶 **balanced** | 15-30 | 1-5 мин | Средний | Стандартный режим |
| 🚀 **aggressive** | 40-80 | 30с-2мин | Высокий | Максимум скорости |

**Авто-даунгрейд:** При риске > threshold режим автоматически понижается:
- aggressive → balanced → reliable

---

## 🔗 Полезные ссылки

- Мини-панель: `https://t.me/your_bot/panel`
- Реферальная ссылка: выдаётся при `/start`
- Поддержка: пишите в бот
