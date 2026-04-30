from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from src.utils.memory import memory
from src.utils.openai_client import openai_client
from src.utils.database import db

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🚀 **Добро пожаловать в GRAMGPT!**\n\n"
        "Я ваш персональный ИИ-помощник с памятью и поддержкой разных моделей.\n\n"
        "**Доступные возможности:**\n"
        "💬 **Чат**: Я помню всё, что мы обсуждали\n"
        "🎨 **Картинки**: /image <описание>\n"
        "⚙️ **Настройки**: /settings (выбор модели)\n"
        "🧹 **Очистка**: /clear"
    )

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "📜 **Список команд:**\n\n"
        "/start - Начать работу\n"
        "/settings - Выбрать модель ИИ\n"
        "/image <описание> - Сгенерировать картинку\n"
        "/clear - Очистить историю\n"
        "/help - Справка"
    )

@router.message(Command("clear"))
async def cmd_clear(message: types.Message):
    memory.clear_history(message.chat.id)
    await message.answer("🧹 История диалога очищена!")

@router.message(Command("settings"))
async def cmd_settings(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="GPT-4o (Мощная)", callback_data="model_gpt-4o"))
    builder.row(types.InlineKeyboardButton(text="GPT-4o-mini (Быстрая)", callback_data="model_gpt-4o-mini"))

    current_model = db.get_user_model(message.chat.id)
    await message.answer(f"⚙️ **Настройки**\n\nТекущая модель: `{current_model}`", reply_markup=builder.as_markup())

@router.callback_query(F.data.startswith("model_"))
async def handle_model_selection(callback: types.CallbackQuery):
    new_model = callback.data.split("_")[1]
    db.set_user_model(callback.message.chat.id, new_model)
    await callback.message.edit_text(f"✅ Модель успешно изменена на: `{new_model}`")
    await callback.answer()

@router.message(Command("image"))
async def cmd_image(message: types.Message, command: CommandObject):
    if not command.args:
        await message.answer("Пожалуйста, введите описание для картинки.")
        return

    await message.bot.send_chat_action(chat_id=message.chat.id, action="upload_photo")
    image_url = await openai_client.generate_image(command.args)

    if image_url.startswith("❌"):
        await message.answer(image_url)
    else:
        await message.answer_photo(photo=image_url, caption=f"🎨 Готово: {command.args}")
