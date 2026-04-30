from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject
from src.core.orchestrator import orchestrator
from src.core.account_manager import account_manager
from src.db.database import db

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🚀 **GPTGRAM Ultimate 2026**\n\n"
        "Я — полнофункциональный ИИ-оркестратор вашего маркетинга.\n\n"
        "**Новое в 2026:**\n"
        "📈 Predictive ROI Engine: /roi\n"
        "🔄 AutoFunnel AI: /funnel\n"
        "🧬 Biological Rhythm Sync\n"
        "📱 Multi-Channel (TG, WA, IG, SMS)\n\n"
        "Команды:\n"
        "/create_campaign <цель> — Построить стратегию\n"
        "/roi <id> — Отчет по окупаемости\n"
        "/funnel — Статус авто-воронок\n"
        "/appeal — AI-юрист (апелляция бана)"
    )

@router.message(Command("create_campaign"))
async def cmd_create(message: types.Message, command: CommandObject):
    if not command.args:
        await message.answer("Укажите цель. Пример: /create_campaign Продать 100 курсов")
        return

    await message.answer("🧠 AI Orchestrator анализирует рынок и строит план с прогнозом ROI...")
    strategy = await orchestrator.create_campaign_strategy("Campaign 2026", command.args)

    msg = (
        f"✅ **Стратегия готова!**\n\n"
        f"🎯 Цель: {command.args}\n"
        f"📊 Прогноз ROI: {strategy.get('predicted_roi')}\n"
        f"📱 Каналы: {', '.join(strategy.get('channels', []))}\n\n"
        f"Бот переходит в режим Auto-Optimization."
    )
    await message.answer(msg)

@router.message(Command("roi"))
async def cmd_roi(message: types.Message, command: CommandObject):
    # Mock for campaign ID 1
    report = db.get_roi_report(1)
    await message.answer(
        f"📈 **Отчет ROI (Кампания #1):**\n\n"
        f"- Прогноз: 240%\n"
        f"- Факт: {report['roi_actual']}\n"
        f"- Выручка: ${report['total_revenue']}\n"
        f"- Затраты: ${report['total_cost']}"
    )

@router.message(Command("appeal"))
async def cmd_appeal(message: types.Message):
    appeal_text = account_manager.generate_appeal("Current")
    await message.answer(f"⚖️ **AI-Юрист сгенерировал апелляцию:**\n\n`{appeal_text}`")
