from aiogram import Router, types
from aiogram.filters import Command, CommandObject
from src.utils.memory import memory
from src.utils.openai_client import openai_client

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🌲 **Welcome to EL Strategy Bot**\n\n"
        "I am your AI mentor for solopreneur business strategy. "
        "I provide depth and practicality that exceeds standard models.\n\n"
        "**Available Commands:**\n"
        "🔍 /strategy - Start a business strategy session\n"
        "🎓 /learn - Explore my skills and training data\n"
        "🎨 /image - Generate an image for your brand\n"
        "🧹 /clear - Reset conversation history\n"
        "📜 /help - Show this help message"
    )

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "📜 **Command List**\n\n"
        "/start - Welcome & intro\n"
        "/strategy <topic> - Get a deep strategy analysis\n"
        "/learn - Understand my capabilities\n"
        "/image <prompt> - Generate AI image\n"
        "/clear - Clear history\n"
        "Just send a message to start chatting!"
    )

@router.message(Command("clear"))
async def cmd_clear(message: types.Message):
    memory.clear_history(message.chat.id)
    await message.answer("🧹 Conversation reset. Ready for a new strategy!")

@router.message(Command("strategy"))
async def cmd_strategy(message: types.Message, command: CommandObject):
    if not command.args:
        await message.answer(
            "🔍 **Start a Strategy Session**\n\n"
            "Please provide your niche or product idea.\n"
            "Example: `/strategy AI courses for designer`"
        )
        return

    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

    prompt = (
        f"Please provide a deep strategy analysis for the following solopreneur idea: {command.args}. "
        "Include Niche Analysis (SWOT, Competitors, Trends), Business Model (Monetization, Funnel), and a high-level Launch Plan."
    )

    # We add this special prompt to memory to maintain the strategy focus
    memory.add_message(message.chat.id, "user", prompt)
    response = await openai_client.get_chat_response(memory.get_history(message.chat.id))
    memory.add_message(message.chat.id, "assistant", response)

    await message.answer(response)

@router.message(Command("image"))
async def cmd_image(message: types.Message, command: CommandObject):
    if not command.args:
        await message.answer("Please provide a prompt for the image.")
        return

    await message.bot.send_chat_action(chat_id=message.chat.id, action="upload_photo")
    image_url = await openai_client.generate_image(command.args)

    if image_url.startswith("❌"):
        await message.answer(image_url)
    else:
        await message.answer_photo(photo=image_url, caption=f"🎨 Brand Asset: {command.args}")
