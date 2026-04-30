from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import WebAppInfo
from src.db.memory import memory
from src.core.openai_client import openai_client
from src.db.database import db
from src.core.referral import referral_system

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message, command: CommandObject):
    if command.args:
        referrer = await referral_system.process_new_user(message.chat.id, command.args)
        if referrer:
            await message.answer("🎁 Вы присоединились по приглашению! Лимиты будут увеличены.")

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(
        text="🚀 Открыть Панель Управления",
        web_app=WebAppInfo(url="https://dist-yentgqay.devinapps.com/panel/index.html")
    ))

    ref_link = referral_system.generate_referral_link(message.chat.id)
    await message.answer(
        "⚡ **GPTGRAM Ultimate 2026**\n\n"
        "Добро пожаловать в будущее маркетинга! "
        "Теперь вы можете управлять всеми кампаниями прямо здесь через Mini App.\n\n"
        "**Ваш статус:**\n"
        "💳 План: Free\n"
        "📊 Лимиты: 100 действий/день\n"
        f"🔗 Ваша реф-ссылка: `{ref_link}`",
        reply_markup=builder.as_markup()
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
