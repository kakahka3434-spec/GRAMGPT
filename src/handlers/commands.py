from aiogram import Router, types
from aiogram.filters import Command, CommandObject
from src.utils.memory import memory
from src.utils.openai_client import openai_client

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🌲 **Добро пожаловать в EL Strategy Bot**\n\n"
        "Я ваш ИИ-ментор по бизнес-стратегии для солопренеров. "
        "Я обеспечиваю глубину и практичность, превосходящие стандартные модели.\n\n"
        "**Доступные команды:**\n"
        "🔍 /strategy - Начать сессию бизнес-стратегии\n"
        "🎓 /learn - Изучить мои навыки и данные обучения\n"
        "🎨 /image - Создать изображение для вашего бренда\n"
        "🧹 /clear - Очистить историю переписки\n"
        "📜 /help - Показать справку"
    )

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "📜 **Список команд**\n\n"
        "/start - Приветствие и введение\n"
        "/strategy <тема> - Глубокий стратегический анализ\n"
        "/learn - Узнать о моих возможностях\n"
        "/image <промпт> - Генерация ИИ-изображения\n"
        "/clear - Очистить историю\n"
        "Просто отправьте сообщение, чтобы начать чат!"
    )

@router.message(Command("clear"))
async def cmd_clear(message: types.Message):
    memory.clear_history(message.chat.id)
    await message.answer("🧹 История очищена. Готов к новой стратегии!")

@router.message(Command("strategy"))
async def cmd_strategy(message: types.Message, command: CommandObject):
    if not command.args:
        await message.answer(
            "🔍 **Начать стратегическую сессию**\n\n"
            "Пожалуйста, укажите вашу нишу или идею продукта.\n"
            "Пример: `/strategy AI курсы для дизайнеров`"
        )
        return

    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

    prompt = (
        f"Пожалуйста, предоставь глубокий стратегический анализ для следующей идеи соло-бизнеса: {command.args}. "
        "Включи анализ ниши (SWOT, конкуренты, тренды), бизнес-модель (монетизация, воронка) и план запуска."
    )

    memory.add_message(message.chat.id, "user", prompt)
    response = await openai_client.get_chat_response(memory.get_history(message.chat.id))
    memory.add_message(message.chat.id, "assistant", response)

    await message.answer(response)

@router.message(Command("image"))
async def cmd_image(message: types.Message, command: CommandObject):
    if not command.args:
        await message.answer("Пожалуйста, введите описание для изображения.")
        return

    await message.bot.send_chat_action(chat_id=message.chat.id, action="upload_photo")
    image_url = await openai_client.generate_image(command.args)

    if image_url.startswith("❌"):
        await message.answer(image_url)
    else:
        await message.answer_photo(photo=image_url, caption=f"🎨 Ассет бренда: {command.args}")
