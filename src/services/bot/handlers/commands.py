from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from src.db.memory import memory
from src.core.openai_client import openai_client
from src.db.database import db
from src.services.parser import smart_parser

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "⚡ **GPTGRAM Ultimate запущен**\n\n"
        "Я — профессиональная система автоматизации с ИИ нового поколения.\n\n"
        "**Мои модули:**\n"
        "🛡️ Anti-Detect 2.0 (Human Emulation)\n"
        "🎯 AI-Таргетинг (Поведенческий анализ)\n"
        "🔄 Авто-воронки (Скоро)\n\n"
        "Команды:\n"
        "/analyze - Анализ поведения (отправьте текст)\n"
        "/settings - Настройки ИИ\n"
        "/image - Генерация графики"
    )

@router.message(Command("analyze"))
async def cmd_analyze(message: types.Message, command: CommandObject):
    if not command.args:
        await message.answer("Пожалуйста, добавьте текст для анализа после команды.")
        return

    await message.answer("🔍 Провожу поведенческий анализ пользователя...")
    analysis = await smart_parser.analyze_user_behavior(command.args)
    await message.answer(f"📊 **Результат анализа:**\n\n{analysis['raw_analysis']}")

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

@router.message(Command("image"))
async def cmd_image(message: types.Message, command: CommandObject):
    if not command.args:
        await message.answer("Введите описание.")
        return
    await message.bot.send_chat_action(chat_id=message.chat.id, action="upload_photo")
    image_url = await openai_client.generate_image(command.args)
    await message.answer_photo(photo=image_url, caption=f"🎨 Готово")
