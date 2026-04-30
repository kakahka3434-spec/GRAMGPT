from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

def get_topics_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔍 Niche Analysis", callback_data="edu_niche"))
    builder.row(types.InlineKeyboardButton(text="💰 Business Model", callback_data="edu_model"))
    builder.row(types.InlineKeyboardButton(text="🚀 Launch Plan", callback_data="edu_launch"))
    builder.row(types.InlineKeyboardButton(text="📊 Training Data Info", callback_data="edu_data"))
    return builder.as_markup()

@router.message(Command("learn"))
async def cmd_learn(message: types.Message):
    await message.answer(
        "🌲 **Welcome to EL Strategy Academy**\n\n"
        "I am EL, your solopreneur strategist. I've been trained on a massive dataset of high-quality business dialogues to help you build a successful solo business. "
        "Choose a module to see how I can help you:",
        reply_markup=get_topics_keyboard()
    )

@router.callback_query(F.data.startswith("edu_"))
async def handle_edu_callback(callback: types.CallbackQuery):
    topic = callback.data.split("_")[1]

    content = {
        "niche": (
            "🔍 **Skill 1: Niche Analysis**\n\n"
            "**What I do:** Market research, pain points, competitor analysis, trend mapping (2024-2026).\n\n"
            "**Example Input:** 'I want to create AI courses for designers.'\n"
            "**Expected Output:** SWOT analysis, list of 5 competitors with pricing, detailed persona profiles, and market trends."
        ),
        "model": (
            "💰 **Skill 2: Business Model**\n\n"
            "**What I do:** Monetization strategy, marketing funnels, unit economics (LTV, CAC).\n\n"
            "**Example Input:** 'Niche: Online productivity coaching.'\n"
            "**Expected Output:** Subscription model structure, tiered pricing, LTV projections, and a lead-to-purchase funnel map."
        ),
        "launch": (
            "🚀 **Skill 3: Launch Plan**\n\n"
            "**What I do:** Step-by-step 12-week roadmap, checklists, and toolkits.\n\n"
            "**Example Input:** 'Product: SaaS for email automation.'\n"
            "**Expected Output:** 12-week timeline, weekly tasks, success metrics, and a list of recommended automation tools."
        ),
        "data": (
            "📊 **My Training Data**\n\n"
            "I have been fine-tuned on **100,000 high-quality examples**:\n"
            "- **20K Base:** High-quality synthetic data (GPT-4o) + manual filtering.\n"
            "- **80K Expansion:** Massively generated with self-verification.\n\n"
            "**Quality over Quantity:** My 100K 'perfect' examples outperform 1M average ones. I am optimized specifically for solopreneur business logic."
        )
    }

    await callback.message.edit_text(
        content.get(topic, "Coming soon!"),
        reply_markup=get_topics_keyboard()
    )
    await callback.answer()
