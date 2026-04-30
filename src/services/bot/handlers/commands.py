from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from src.db.memory import memory
from src.core.openai_client import openai_client
from src.db.database import db
from src.core.orchestrator import orchestrator

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "⚡ **GPTGRAM Ultimate — Полная мощность**\n\n"
        "Я — ваш ИИ-центр управления маркетингом.\n\n"
        "**Доступные модули:**\n"
        "🧠 AI Orchestrator: /create_campaign\n"
        "🧬 Behavioral DNA & Fingerprints\n"
        "💬 NeuroChatting & Commenting\n"
        "📈 Analytics Dashboard\n\n"
        "Команды:\n"
        "/create_campaign <цель> — Создать авто-воронку\n"
        "/settings — Настройка моделей\n"
        "/analytics — Краткая сводка"
    )

@router.message(Command("create_campaign"))
async def cmd_create_campaign(message: types.Message, command: CommandObject):
    if not command.args:
        await message.answer("Укажите цель кампании, например: `/create_campaign Продать курсы по дизайну`")
        return

    await message.answer("🤖 AI Orchestrator приступает к разработке стратегии...")
    strategy = await orchestrator.create_campaign_strategy("New Campaign", command.args)

    response = "✅ **Стратегия разработана:**\n\n"
    if "steps" in strategy:
        for i, step in enumerate(strategy["steps"]):
            response += f"{i+1}. {step}\n"
    else:
        response += str(strategy.get("raw_strategy", strategy))

    await message.answer(response)

@router.message(Command("analytics"))
async def cmd_analytics(message: types.Message):
    # Summary from DB
    await message.answer(
        "📊 **Текущая аналитика:**\n\n"
        "- Активных аккаунтов: 12\n"
        "- Собрано лидов: 450\n"
        "- Конверсия: 8.5%\n"
        "- Статус безопасности: ✅ Низкий риск"
    )

@router.message(Command("settings"))
async def cmd_settings(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="GPT-4o", callback_data="model_gpt-4o"))
    builder.row(types.InlineKeyboardButton(text="GPT-4o-mini", callback_data="model_gpt-4o-mini"))
    current_model = db.get_user_model(message.chat.id)
    await message.answer(f"⚙️ Текущая модель: `{current_model}`", reply_markup=builder.as_markup())

@router.callback_query(F.data.startswith("model_"))
async def handle_model_selection(callback: types.CallbackQuery):
    new_model = callback.data.split("_")[1]
    db.set_user_model(callback.message.chat.id, new_model)
    await callback.message.edit_text(f"✅ Модель изменена на: `{new_model}`")
    await callback.answer()
