from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import WebAppInfo
from src.db.memory import memory
from src.core.openai_client import openai_client
from src.db.database import db
from src.core.referral import referral_system
from src.core.avatar import avatar_engine

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message, command: CommandObject):
    if command.args:
        referrer = await referral_system.process_new_user(message.chat.id, command.args)
        if referrer:
            await message.answer("🎁 Вы присоединились по приглашению! Лимиты будут увеличены.")

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(
        text="🚀 Открыть Панель (Mini App)",
        web_app=WebAppInfo(url="https://gptgram-ultimate-demo.onrender.com/panel/index.html")
    ))

    ref_link = referral_system.generate_referral_link(message.chat.id)
    await message.answer(
        "⚡ **GPTGRAM Ultimate — Creative Studio**\n\n"
        "Вы используете самую мощную систему маркетинга.\n\n"
        "**Новые фичи:**\n"
        "🎭 AI Video Avatars: /video <текст>\n"
        "🎤 Voice Cloning (Auto)\n"
        "📦 Marketplace: /templates\n\n"
        f"🔗 Ваша реф-ссылка: `{ref_link}`",
        reply_markup=builder.as_markup()
    )

@router.message(Command("video"))
async def cmd_video(message: types.Message, command: CommandObject):
    if not command.args:
        await message.answer("Введите текст для видео-ответа аватара.")
        return

    await message.answer("🎬 Генерирую видео-сообщение с вашим AI-аватаром... (HeyGen Integration)")
    video_url = await avatar_engine.generate_video_response(command.args)
    await message.answer_video(video=video_url, caption="🎬 Ваш видео-ответ готов!")

@router.message(Command("templates"))
async def cmd_templates(message: types.Message):
    await message.answer(
        "🛒 **Marketplace шаблонов**\n\n"
        "1. Crypto Investor Funnel — 5 TON\n"
        "2. Design Agency Outreach — 3.5 TON\n"
        "3. SaaS B2B Drip — 10 TON\n\n"
        "Покупка доступна в Mini App."
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
