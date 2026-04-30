from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

def get_topics_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔍 Анализ ниши", callback_data="edu_niche"))
    builder.row(types.InlineKeyboardButton(text="💰 Бизнес-модель", callback_data="edu_model"))
    builder.row(types.InlineKeyboardButton(text="🚀 План запуска", callback_data="edu_launch"))
    builder.row(types.InlineKeyboardButton(text="📊 Данные обучения", callback_data="edu_data"))
    return builder.as_markup()

@router.message(Command("learn"))
async def cmd_learn(message: types.Message):
    await message.answer(
        "🌲 **Добро пожаловать в Академию Стратегии EL**\n\n"
        "Я — EL, ваш стратег для соло-бизнеса. Я был обучен на огромном датасете высококачественных бизнес-диалогов. "
        "Выберите модуль, чтобы узнать, как я могу вам помочь:",
        reply_markup=get_topics_keyboard()
    )

@router.callback_query(F.data.startswith("edu_"))
async def handle_edu_callback(callback: types.CallbackQuery):
    topic = callback.data.split("_")[1]
    content = {
        "niche": (
            "🔍 **Навык 1: Анализ ниши**\n\n"
            "**Что я делаю:** Исследование рынка, выявление болей, анализ конкурентов, тренды (2024-2026).\n\n"
            "**Пример входа:** 'Хочу делать AI курсы для дизайнеров.'\n"
            "**Пример выхода:** SWOT-анализ, список 5 конкурентов с ценами, портреты ЦА и тренды рынка."
        ),
        "model": (
            "💰 **Навык 2: Бизнес-модель**\n\n"
            "**Что я делаю:** Стратегия монетизации, маркетинговые воронки, юнит-экономика (LTV, CAC).\n\n"
            "**Пример входа:** 'Ниша: онлайн-коучинг по продуктивности.'\n"
            "**Пример выхода:** Структура модели подписки, уровни цен, прогнозы LTV и карта воронки продаж."
        ),
        "launch": (
            "🚀 **Навык 3: План запуска**\n\n"
            "**Что я делаю:** Пошаговая 12-недельная дорожная карта, чек-листы и наборы инструментов.\n\n"
            "**Пример входа:** 'Продукт: SaaS для автоматизации email.'\n"
            "**Пример выхода:** 12-недельный график, еженедельные задачи, метрики успеха и список инструментов автоматизации."
        ),
        "data": (
            "📊 **Мои данные обучения**\n\n"
            "Я был дообучен на **100 000 высококачественных примерах**:\n"
            "- **20K База:** Высококачественная синтетика (GPT-4o) + ручная фильтрация.\n"
            "- **80K Расширение:** Массовая генерация с самопроверкой.\n\n"
            "**Качество важнее количества:** Мои 100K 'идеальных' примеров бьют 1М средних. Я оптимизирован специально для бизнес-логики солопренеров."
        )
    }
    await callback.message.edit_text(content.get(topic, "Скоро будет!"), reply_markup=get_topics_keyboard())
    await callback.answer()
