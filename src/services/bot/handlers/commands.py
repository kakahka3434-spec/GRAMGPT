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
            await message.answer("Вы присоединились по приглашению! Лимиты будут увеличены.")

    builder = InlineKeyboardBuilder()

    ref_link = referral_system.generate_referral_link(message.chat.id)
    await message.answer(
        "**GRAMGPT — ИИ-комбайн для Telegram**\n\n"
        "Продвижение с помощью нейросетей нового поколения.\n\n"
        "**Возможности:**\n"
        "- Нейрокомментинг и нейрочаттинг\n"
        "- Парсинг целевой аудитории\n"
        "- Прогрев аккаунтов\n"
        "- Массовые реакции\n"
        "- Генерация изображений\n\n"
        "**Команды:**\n"
        "`/image <описание>` — Генерация изображения\n"
        "`/settings` — Выбор модели ИИ\n"
        "`/clear` — Очистка истории\n"
        "`/help` — Справка\n\n"
        f"Ваша реф-ссылка: `{ref_link}`",
        reply_markup=builder.as_markup()
    )


@router.message(Command("image"))
async def cmd_image(message: types.Message, command: CommandObject):
    if not command.args:
        await message.answer("Укажите описание изображения.\nПример: `/image космический город будущего`")
        return

    await message.bot.send_chat_action(chat_id=message.chat.id, action="upload_photo")
    image_url = await openai_client.generate_image(command.args)

    if image_url.startswith("http"):
        await message.answer_photo(photo=image_url, caption=f"Изображение по запросу: _{command.args}_")
    else:
        await message.answer(image_url)


@router.message(Command("clear"))
async def cmd_clear(message: types.Message):
    memory.clear_history(message.chat.id)
    await message.answer("История диалога очищена.")


@router.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "**GRAMGPT — Справка**\n\n"
        "**Основные команды:**\n"
        "`/start` — Запуск бота и приветствие\n"
        "`/image <описание>` — Генерация изображения (DALL-E 3)\n"
        "`/settings` — Выбор модели ИИ (GPT-4o / GPT-4o-mini)\n"
        "`/clear` — Очистка истории диалога\n"
        "`/help` — Эта справка\n\n"
        "**Как общаться:**\n"
        "Просто отправьте текстовое сообщение — бот ответит с помощью ИИ.\n"
        "Можно отправить фото — бот проанализирует изображение.\n"
        "Можно отправить голосовое — бот распознает речь и ответит.\n\n"
        "**Модели:**\n"
        "• GPT-4o — максимальное качество\n"
        "• GPT-4o-mini — быстрые ответы, экономия токенов"
    )


@router.message(Command("settings"))
async def cmd_settings(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="GPT-4o", callback_data="model_gpt-4o"))
    builder.row(types.InlineKeyboardButton(text="GPT-4o-mini", callback_data="model_gpt-4o-mini"))
    current_model = db.get_user_model(message.chat.id)
    await message.answer(f"Текущая модель: `{current_model}`\nВыберите модель:", reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("model_"))
async def handle_model_selection(callback: types.CallbackQuery):
    new_model = callback.data.removeprefix("model_")
    db.set_user_model(callback.message.chat.id, new_model)
    await callback.message.edit_text(f"Модель изменена на: `{new_model}`")
    await callback.answer()
