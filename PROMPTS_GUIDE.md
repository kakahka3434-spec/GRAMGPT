# 🎯 GRAMGPT ULTIMATE — PROMPT ENGINEERING GUIDE
## Коллекция промптов для всех AI-модулей системы

---

## 📋 СОДЕРЖАНИЕ

1. [System Prompts](#system-prompts)
2. [Comment Generation](#comment-generation)
3. [Spam Detection](#spam-detection)
4. [Tone Matching](#tone-matching)
5. [Crisis Management](#crisis-management)
6. [Analytics Insights](#analytics-insights)
7. [Multi-language Support](#multi-language-support)

---

## 🤖 SYSTEM PROMPTS

### Базовый системный промпт (GRAMGPT Persona)

```python
SYSTEM_PROMPT = """
Вы — GRAMGPT Ultimate, продвинутая AI-система для автоматизации маркетинга в Telegram.

ВАШИ ВОЗМОЖНОСТИ:
• Генерация естественных комментариев под постами
• Анализ тональности и стиля текста
• Адаптация под контекст обсуждения
• Соблюдение безопасности (anti-spam, anti-ban)
• Мультиязычная поддержка (RU/EN/ES/DE)

ВАШ СТИЛЬ:
• Естественный, человеческий язык
• Без излишней формальности
• Кратко и по делу (максимум 150 символов для комментариев)
• Эмодзи уместно и умеренно (1-2 на комментарий)
• Без агрессивных продаж

ПРИОРИТЕТЫ:
1. Безопасность аккаунта пользователя (не спамить)
2. Релевантность контексту
3. Естественность формулировок
4. Полезность для читателей

ЗАПРЕЩЕНО:
• ALL CAPS фразы
• Множественные восклицательные знаки (!!!)
• Агрессивные призывы к действию (BUY NOW, CLICK HERE)
• Обещания быстрых денег
• Спам-ключевики (free money, passive income, work from home)

Отвечайте на языке пользователя. Будьте кратки и профессиональны.
"""
```

---

## 💬 COMMENT GENERATION

### Промпт для генерации комментария (Context-Aware)

```python
COMMENT_GENERATION_PROMPT = """
Сгенерируй естественный комментарий для Telegram-поста.

КОНТЕКСТ ПОСТА:
{post_text}

ТЕМА КАНАЛА:
{channel_topic}

ЦЕЛЬ КОММЕНТАРИЯ:
{goal}  # engagement, promo, support, expert_opinion

ТРЕБОВАНИЯ:
1. Длина: 80-150 символов
2. Стиль: {tone}  # friendly, professional, casual, expert
3. Язык: тот же, что и пост
4. Структура:
   - Начать с реакции на контент (похвала, вопрос, дополнение)
   - Добавить ценность (инсайт, опыт, ресурс)
   - Завершить естественно (без агрессивного CTA)
5. Если есть ссылка для продвижения: {target_link}
   - Вплести органично в конце
   - Не делать её центром комментария
   - Использовать мягкие формулировки ("может пригодиться", "делюсь")

ПРИМЕРЫ ХОРОШИХ КОММЕНТАРИЕВ:
✅ "Интересный взгляд! Мы недавно решали похожую задачу через автоматизацию — сэкономили 10+ часов. Может пригодиться: {link}"
✅ "Классный разбор 👍 Кстати, по этой теме собрали чек-лист из 15 пунктов, чтобы не упустить важное: {link}"
✅ "Согласен с основным тезисом! Удалось достичь результата за 2 недели с помощью одного подхода, делюсь: {link}"

ПЛОХИЕ ПРИМЕРЫ (НЕ ДЕЛАТЬ ТАК):
❌ "КУПИ ПРЯМО СЕЙЧАС!!! ЛУЧШЕЕ ПРЕДЛОЖЕНИЕ!!!"
❌ "Заработай $5000 в день пассивно! ЖМИ СЮДА: {link}"
❌ "WORK FROM HOME!!! AMAZING OFFER!!!"

Сгенерируй ОДИН комментарий, готовый к публикации:
"""
```

### Промпт для Sniper Mode (Emoji + Edit)

```python
SNIPER_EMOJI_PROMPT = """
Выбери подходящий эмодзи для быстрой реакции на пост.

ПОСТ:
{post_text}

ТОН ПОСТА:
{tone}  # positive, neutral, serious, celebratory, informative

ПРАВИЛА:
1. Выбрать ОДИН эмодзи
2. Должен соответствовать тону
3. Без иронии и сарказма
4. Универсально понятный

СПИСОК РАЗРЕШЁННЫХ ЭМОДЗИ:
👍 🔥 👏 💯 🎯 ✅ 🚀 💪 😊 🤔 💡 ⭐ 🙌 🎉

Верни ТОЛЬКО эмодзи без дополнительного текста:
"""

SNIPER_EDIT_PROMPT = """
Сгенерируй промо-комментарий для редактирования после эмодзи-реакции.

ИСХОДНЫЙ ПОСТ:
{post_text}

ССЫЛКА ДЛЯ ПРОДВИЖЕНИЯ:
{target_link}

ОСОБЫЕ ТРЕБОВАНИЯ (Sniper Mode):
1. Это будет РЕДАКТИРОВАНИЕ эмодзи, а не новый комментарий
2. Поэтому должно выглядеть как развитие мысли
3. Можно использовать формулировки "Кстати...", "Дополню...", "Развивая тему..."
4. Длина: 100-180 символов (можно чуть длиннее обычного)
5. Ссылка должна быть органичной частью сообщения

СТРУКТУРА:
- Связка с предыдущим контекстом (эмодзи был реакцией)
- Добавление ценности (инсайт, ресурс, опыт)
- Натуральное упоминание ссылки

ПРИМЕРЫ:
✅ "Кстати, дополню по теме — мы автоматизировали этот процесс и экономим 10+ часов в неделю. Делюсь опытом: {link}"
✅ "Развивая мысль — собрали чек-лист из 15 пунктов для этого направления. Может пригодиться: {link}"
✅ "Дополню из практики — удалось достичь результата за 2 недели с таким подходом. Кейс здесь: {link}"

Сгенерируй комментарий:
"""
```

---

## 🛡️ SPAM DETECTION

### Промпт для оценки спама (AI-powered validation)

```python
SPAM_DETECTION_PROMPT = """
Проанализируй текст комментария на признаки спама.

ТЕКСТ ДЛЯ ПРОВЕРКИ:
{text}

КРИТЕРИИ ОЦЕНКИ (0-10 баллов каждый):
1. Caps Ratio — доля ЗАГЛАВНЫХ букв (>30% = плохо)
2. Exclamation Density — количество восклицательных знаков (>3 = плохо)
3. Link Density — плотность ссылок (>1 на 100 символов = плохо)
4. Spam Keywords — наличие спам-фраз:
   - BUY NOW, CLICK HERE, ACT NOW
   - FREE MONEY, PASSIVE INCOME
   - WORK FROM HOME, EARN $X PER DAY
   - LIMITED TIME, AMAZING OFFER
5. Aggressive CTA — навязчивые призывы к действию
6. Repetition — повторение одинаковых фраз
7. Relevance — соответствие контексту (если известен)

ФОРМАТ ОТВЕТА:
Верни JSON:
{
  "spam_score": 0-100,  # общий балл (0-30 = безопасно, 31-60 = риск, 61+ = спам)
  "caps_score": 0-10,
  "exclamation_score": 0-10,
  "link_score": 0-10,
  "keyword_score": 0-10,
  "cta_score": 0-10,
  "repetition_score": 0-10,
  "relevance_score": 0-10,
  "detected_keywords": ["список найденных спам-фраз"],
  "recommendation": "approve" | "revise" | "reject",
  "suggestions": ["список рекомендаций по улучшению"]
}

Пример ответа:
{
  "spam_score": 25,
  "caps_score": 2,
  "exclamation_score": 1,
  "link_score": 3,
  "keyword_score": 0,
  "cta_score": 4,
  "repetition_score": 0,
  "relevance_score": 8,
  "detected_keywords": [],
  "recommendation": "approve",
  "suggestions": []
}
"""
```

---

## 🎭 TONE MATCHING

### Промпт для анализа тональности поста

```python
TONE_ANALYSIS_PROMPT = """
Проанализируй тон и стиль Telegram-поста.

ТЕКСТ ПОСТА:
{post_text}

ЗАДАЧА:
Определить характеристики текста для адаптации ответа.

ВЕРНИ JSON:
{
  "primary_tone": "friendly" | "professional" | "casual" | "serious" | "celebratory" | "informative" | "controversial",
  "secondary_tone": "...",  # опционально
  "formality_level": 1-5,  # 1=очень неформальный, 5=очень формальный
  "emotion_level": 1-5,  # 1=нейтральный, 5=эмоциональный
  "language": "ru" | "en" | "es" | "de" | "other",
  "key_topics": ["список основных тем"],
  "writing_style": {
    "sentence_length": "short" | "medium" | "long",
    "uses_emoji": true/false,
    "uses_questions": true/false,
    "uses_lists": true/false
  },
  "recommended_response_tone": "friendly" | "professional" | "casual" | "expert",
  "recommended_emoji_usage": "none" | "minimal" | "moderate" | "active"
}

Пример ответа:
{
  "primary_tone": "informative",
  "secondary_tone": "friendly",
  "formality_level": 3,
  "emotion_level": 2,
  "language": "ru",
  "key_topics": ["автоматизация", "маркетинг", "Telegram"],
  "writing_style": {
    "sentence_length": "medium",
    "uses_emoji": true,
    "uses_questions": false,
    "uses_lists": true
  },
  "recommended_response_tone": "professional",
  "recommended_emoji_usage": "moderate"
}
"""
```

### Промпт для адаптации стиля ответа

```python
STYLE_ADAPTATION_PROMPT = """
Адаптируй стиль комментария под тон исходного поста.

ХАРАКТЕРИСТИКИ ПОСТА:
{tone_analysis_json}

ЧЕРНОВИК КОММЕНТАРИЯ:
{draft_comment}

ЗАДАЧА:
Переписать комментарий, сохраняя смысл, но адаптируя:
1. Тон (friendly/professional/casual)
2. Уровень формальности
3. Использование эмодзи
4. Длину предложений
5. Лексику (соответствует языку поста)

ПРАВИЛА:
- Сохранить основную мысль и ссылку (если есть)
- Не добавлять новую информацию
- Сделать так, будто комментарий написан тем же человеком/аудиторией
- Длина: ±20% от оригинала

ВЕРНИ адаптированный комментарий (только текст):
"""
```

---

## 🚨 CRISIS MANAGEMENT

### Промпт для обнаружения кризисных ситуаций

```python
CRISIS_DETECTION_PROMPT = """
Проанализируй метрики аккаунта на признаки проблем.

МЕЕТРИКИ АККАУНТА:
{account_metrics_json}

ИСТОРИЯ ДЕЙСТВИЙ (последние 24 часа):
{recent_actions}

ТЕКУЩИЕ ОГРАНИЧЕНИЯ:
{current_limits}

СИМПТОМЫ ДЛЯ АНАЛИЗА:
1. FloodWait ошибки — частота и длительность
2. Rate limit превышения
3. Failed actions процент
4. Reports/Jam complaints (если доступны)
5. Резкое изменение паттернов активности
6. Time-based аномалии (действия в необычное время)

ВЕРНИ JSON:
{
  "crisis_detected": true/false,
  "crisis_type": "flood" | "rate_limit" | "spam_reports" | "suspicious_activity" | "none",
  "severity": "low" | "medium" | "high" | "critical",
  "confidence": 0-100,  # уверенность детекции
  "indicators": [
    {
      "name": "название индикатора",
      "value": "текущее значение",
      "threshold": "пороговое значение",
      "status": "normal" | "warning" | "critical"
    }
  ],
  "recommended_actions": [
    {
      "action": "pause" | "reduce_frequency" | "switch_proxy" | "cooldown" | "manual_review",
      "duration_minutes": 0,
      "priority": "immediate" | "soon" | "optional",
      "reason": "обоснование"
    }
  ],
  "estimated_recovery_time_minutes": 0
}

Пример ответа:
{
  "crisis_detected": true,
  "crisis_type": "flood",
  "severity": "medium",
  "confidence": 85,
  "indicators": [
    {
      "name": "flood_wait_count",
      "value": 5,
      "threshold": 3,
      "status": "warning"
    },
    {
      "name": "failed_actions_percent",
      "value": 25,
      "threshold": 15,
      "status": "warning"
    }
  ],
  "recommended_actions": [
    {
      "action": "cooldown",
      "duration_minutes": 120,
      "priority": "immediate",
      "reason": "Multiple FloodWait errors detected"
    },
    {
      "action": "reduce_frequency",
      "duration_minutes": 1440,
      "priority": "soon",
      "reason": "Prevent further rate limiting"
    }
  ],
  "estimated_recovery_time_minutes": 120
}
"""
```

### Промпт для генерации плана восстановления

```python
RECOVERY_PLAN_PROMPT = """
Создай пошаговый план восстановления аккаунта после кризиса.

ТИП КРИЗИСА:
{crisis_type}

ТЕКУЩЕЕ СОСТОЯНИЕ:
{current_state}

ОГРАНИЧЕНИЯ:
{limitations}

ЦЕЛЬ:
Минимизировать простой, предотвратить повторение, восстановить нормальную работу.

ВЕРНИ ПОШАГОВЫЙ ПЛАН:
{
  "phase_1_immediate": {
    "duration_minutes": 0,
    "actions": [
      {"step": 1, "action": "что делать", "rationale": "почему"}
    ]
  },
  "phase_2_stabilization": {
    "duration_hours": 0,
    "actions": [...]
  },
  "phase_3_gradual_return": {
    "duration_days": 0,
    "actions": [...],
    "ramp_up_schedule": {
      "day_1": "X% от нормальной активности",
      "day_2": "Y%",
      "day_3": "Z%"
    }
  },
  "prevention_measures": [
    "меры для предотвращения повторения"
  ],
  "monitoring_indicators": [
    "за чем следить в процессе восстановления"
  ]
}
"""
```

---

## 📊 ANALYTICS INSIGHTS

### Промпт для анализа эффективности кампаний

```python
CAMPAIGN_ANALYSIS_PROMPT = """
Проанализируй результаты маркетинговой кампании в Telegram.

ДАННЫЕ КАМПАНИИ:
{campaign_data_json}

МЕТРИКИ:
- Отправлено комментариев: {comments_sent}
- Успешных (не удалены): {successful}
- Получено реакций: {reactions_received}
- Переходов по ссылке: {clicks}
- Конверсий: {conversions}
- Период: {date_range}

ЗАДАЧА:
1. Оценить общую эффективность
2. Выявить лучшие и худшие паттерны
3. Дать рекомендации по оптимизации

ВЕРНИ JSON:
{
  "overall_score": 0-100,
  "success_rate": 0-100,
  "engagement_rate": 0-100,
  "conversion_rate": 0-100,
  "best_performing": {
    "time_of_day": "HH:MM",
    "comment_style": "описание стиля",
    "channels": ["список каналов"],
    "avg_engagement": 0
  },
  "worst_performing": {...},
  "patterns_detected": [
    "выявленные закономерности"
  ],
  "recommendations": [
    {
      "priority": "high" | "medium" | "low",
      "action": "что изменить",
      "expected_impact": "ожидаемый эффект"
    }
  ],
  "forecast": {
    "next_week_comments": "прогноз количества",
    "next_week_success_rate": "прогноз %"
  }
}
"""
```

---

## 🌍 MULTI-LANGUAGE SUPPORT

### Промпт для определения языка и адаптации

```python
LANGUAGE_DETECTION_PROMPT = """
Определи язык текста и культурные особенности.

ТЕКСТ:
{text}

ВЕРНИ JSON:
{
  "detected_language": "ru" | "en" | "es" | "de" | "fr" | "it" | "pt" | "zh" | "ja" | "other",
  "confidence": 0-100,
  "dialect_variant": "например: ru-RU, en-US, en-GB, es-ES, es-MX",
  "cultural_notes": [
    "особенности коммуникации для этой культуры"
  ],
  "formality_expectations": "высокая" | "средняя" | "низкая",
  "emoji_appropriateness": "high" | "medium" | "low",
  "taboo_topics": [
    "темы, которых лучше избегать"
  ],
  "recommended_adaptations": [
    "рекомендации по адаптации стиля"
  ]
}
"""
```

### Промпт для перевода с адаптацией

```python
TRANSLATION_ADAPTATION_PROMPT = """
Переведи комментарий с адаптацией под целевую культуру.

ОРИГИНАЛ ({source_language}):
{original_text}

ЦЕЛЕВОЙ ЯЗЫК:
{target_language}

ЦЕЛЬ:
Сохранить смысл, тон и намерение, но сделать текст естественным для носителей целевого языка.

ОСОБЫЕ ТРЕБОВАНИЯ:
1. Идиомы и метафоры — адаптировать, не переводить дословно
2. Юмор — заменять на эквивалентный в целевой культуре
3. Формальность — соответствовать ожиданиям
4. Ссылки — оставить как есть
5. Эмодзи — проверить уместность в целевой культуре

ВЕРНИ переведённый текст (только результат):
"""
```

---

## 🧠 FEW-SHOT LEARNING

### Промпт для обучения на успешных примерах

```python
FEWSHOT_GENERATION_PROMPT = """
Сгенерируй комментарий, обучаясь на успешных примерах.

КОНТЕКСТ НОВОГО ПОСТА:
{new_post_text}

ПРИМЕРЫ УСПЕШНЫХ КОММЕНТАРИЕВ (получили много реакций, не были удалены):

Пример 1:
Пост: {example_1_post}
Комментарий: {example_1_comment}
Реакций: {example_1_reactions}
Результат: {example_1_result}

Пример 2:
Пост: {example_2_post}
Комментарий: {example_2_comment}
Реакций: {example_2_reactions}
Результат: {example_2_result}

Пример 3:
Пост: {example_3_post}
Комментарий: {example_3_comment}
Реакций: {example_3_reactions}
Результат: {example_3_result}

АНАЛИЗ ПАТТЕРНОВ:
- Какие слова/фразы встречаются в успешных комментариях?
- Какой тон преобладает?
- Как встроены ссылки?
- Какая длина оптимальна?
- Какие эмодзи используются?

ЗАДАЧА:
Сгенерировать новый комментарий для поста выше, используя выявленные паттерны.

ВЕРНИ комментарий (только текст):
"""
```

---

## 📈 RAG ENGINE INTEGRATION

### Промпт для использования базы знаний

```python
RAG_ENHANCED_PROMPT = """
Сгенерируй комментарий, используя релевантные знания из базы.

КОНТЕКСТ ПОСТА:
{post_text}

НАЙДЕННЫЕ РЕЛЕВАНТНЫЕ ЗНАНИЯ (из RAG):
{retrieved_knowledge_chunks}

ИСТОРИЯ УСПЕШНЫХ КОММЕНТАРИЕВ (из памяти):
{successful_comments_history}

ТЕКУЩИЙ КОНТЕКСТ ДИАЛОГА (если есть):
{conversation_context}

ЗАДАЧА:
1. Использовать знания из RAG для добавления экспертной ценности
2. Учесть историю успешных комментариев для стиля
3. Сохранить естественность и релевантность
4. Интегрировать ссылку (если предоставлена): {target_link}

ВЕРНИ комментарий (максимум 180 символов):
"""
```

---

## 🎯 A/B TESTING

### Промпт для генерации вариантов для теста

```python
AB_TEST_VARIANTS_PROMPT = """
Сгенерируй несколько вариантов комментария для A/B теста.

КОНТЕКСТ ПОСТА:
{post_text}

ЦЕЛЬ ТЕСТА:
{test_goal}  # engagement, clicks, conversions

ПАРАМЕТРЫ ВАРИАЦИИ:
1. Tone: {tones_to_test}  # например: friendly vs professional
2. Hook type: {hook_types}  # вопрос vs утверждение vs комплимент
3. CTA strength: {cta_levels}  # soft vs medium vs strong
4. Emoji usage: {emoji_options}  # none vs minimal vs moderate
5. Link placement: {link_positions}  # начало vs середина vs конец

СГЕНЕРИРУЙ N ВАРИАНТОВ (где N = количество комбинаций):
[
  {
    "variant_id": "A",
    "text": "текст комментария",
    "characteristics": {
      "tone": "...",
      "hook_type": "...",
      "cta_strength": "...",
      "emoji_count": 0,
      "link_position": "..."
    },
    "hypothesis": "почему этот вариант может сработать"
  },
  ...
]

Каждый вариант должен быть уникальным по комбинации характеристик.
"""
```

---

## 📝 USAGE EXAMPLES

### Пример использования в коде

```python
from src.core.ai_client import ai_client

# Генерация комментария с tone matching
async def generate_smart_comment(post_text: str, target_link: str = ""):
    # 1. Анализ тона поста
    tone_prompt = TONE_ANALYSIS_PROMPT.format(post_text=post_text)
    tone_analysis = await ai_client.generate(tone_prompt, max_tokens=500)
    
    # 2. Генерация черновика
    comment_prompt = COMMENT_GENERATION_PROMPT.format(
        post_text=post_text[:500],
        channel_topic="marketing",
        goal="promo",
        tone="professional",
        target_link=target_link or ""
    )
    draft_comment = await ai_client.generate(comment_prompt, max_tokens=200)
    
    # 3. Адаптация стиля
    style_prompt = STYLE_ADAPTATION_PROMPT.format(
        tone_analysis_json=tone_analysis,
        draft_comment=draft_comment
    )
    final_comment = await ai_client.generate(style_prompt, max_tokens=200)
    
    # 4. Проверка на спам
    spam_prompt = SPAM_DETECTION_PROMPT.format(text=final_comment)
    spam_analysis = await ai_client.generate(spam_prompt, max_tokens=500)
    
    if spam_analysis.get("recommendation") == "reject":
        # Перегенерировать
        return await generate_smart_comment(post_text, target_link)
    
    return final_comment
```

---

*Версия: 1.0*
*Обновлено: 2025-01-15*
*Статус: Ready for Implementation*
