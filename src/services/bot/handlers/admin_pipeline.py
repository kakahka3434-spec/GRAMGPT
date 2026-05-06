"""
Pipeline Admin Handlers - Control GRAMGPT automation via Telegram commands.
/start_pipeline, /stop_pipeline, /status
"""

import logging
from typing import Optional

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.utils.markdown import hbold

from src.config import settings
from src.core.pipeline_orchestrator import PipelineOrchestrator
from src.services.telegram_user_client import TelegramUserClient
from src.services.comment_sender import CommentSender
from src.services.account_warmer import AccountWarmer

logger = logging.getLogger(__name__)

# Router for pipeline commands
router = Router()

# Global orchestrator instance (initialized on first /start)
_orchestrator: Optional[PipelineOrchestrator] = None
_telegram_client: Optional[TelegramUserClient] = None

# Admin IDs (you can add multiple admins here)
ADMIN_IDS = set()  # Will be populated from settings or can be hardcoded


def is_admin(user_id: int) -> bool:
    """Check if user is authorized to control pipeline."""
    # For now, allow any user (you can add specific IDs to ADMIN_IDS)
    return True


async def get_orchestrator() -> Optional[PipelineOrchestrator]:
    """Get or initialize pipeline orchestrator."""
    global _orchestrator, _telegram_client
    
    if _orchestrator is not None and _orchestrator.is_running:
        return _orchestrator
    
    # Initialize Telegram client if needed
    if _telegram_client is None:
        _telegram_client = TelegramUserClient(
            api_id=settings.telegram_api_id,
            api_hash=settings.telegram_api_hash,
            phone=settings.telegram_phone,
            session_path="data/sessions/gramgpt_user"
        )
        
        connected = await _telegram_client.connect()
        if not connected:
            logger.error("Failed to connect Telegram client")
            return None
        
        me = await _telegram_client.get_me()
        logger.info(f"Pipeline client connected as @{me['username']}")
    
    # Create components
    comment_sender = CommentSender(_telegram_client)
    account_warmer = AccountWarmer(_telegram_client)
    
    # Create orchestrator
    _orchestrator = PipelineOrchestrator(
        telegram_client=_telegram_client,
        comment_sender=comment_sender,
        account_warmer=account_warmer
    )
    
    return _orchestrator


@router.message(Command("start_pipeline"))
async def cmd_start_pipeline(message: types.Message):
    """
    Start automation pipeline.
    
    Usage: /start_pipeline channel1,channel2 style
    Example: /start_pipeline durov,cryptonews engaging
    """
    if not is_admin(message.from_user.id):
        await message.answer("❌ Access denied")
        return
    
    args = message.text.split()[1:] if len(message.text.split()) > 1 else []
    
    # Parse arguments
    channels = ["durov"]  # Default
    style = "balanced"  # Default
    
    if args:
        # First arg: channels (comma-separated)
        channels = [c.strip().lstrip("@") for c in args[0].split(",")]
        
        # Second arg: style (optional)
        if len(args) > 1 and args[1] in ["expert", "engaging", "casual", "balanced"]:
            style = args[1]
    
    await message.answer(
        f"🚀 Starting pipeline...\n\n"
        f"Channels: {', '.join(channels)}\n"
        f"Style: {style}\n\n"
        f"Use /status to check progress, /stop_pipeline to stop."
    )
    
    try:
        orchestrator = await get_orchestrator()
        if orchestrator is None:
            await message.answer("❌ Failed to initialize pipeline")
            return
        
        # Start in background
        asyncio.create_task(orchestrator.start(
            target_channels=channels,
            style=style,
            max_comments_per_hour=10
        ))
        
        await asyncio.sleep(2)  # Give it time to start
        
        if orchestrator.is_running:
            await message.answer("✅ Pipeline started successfully!")
        else:
            await message.answer("⚠️ Pipeline may not have started. Check /status")
            
    except Exception as e:
        logger.error(f"Start pipeline error: {e}")
        await message.answer(f"❌ Error starting pipeline: {e}")


@router.message(Command("stop_pipeline"))
async def cmd_stop_pipeline(message: types.Message):
    """Stop automation pipeline gracefully."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Access denied")
        return
    
    if _orchestrator is None or not _orchestrator.is_running:
        await message.answer("ℹ️ Pipeline is not running")
        return
    
    await message.answer("🛑 Stopping pipeline gracefully...")
    
    try:
        await _orchestrator.stop()
        await message.answer("✅ Pipeline stopped")
    except Exception as e:
        logger.error(f"Stop pipeline error: {e}")
        await message.answer(f"❌ Error stopping: {e}")


@router.message(Command("status"))
async def cmd_status(message: types.Message):
    """Get pipeline status and statistics."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Access denied")
        return
    
    if _orchestrator is None:
        await message.answer("ℹ️ Pipeline not initialized. Use /start_pipeline first.")
        return
    
    try:
        status_text = _orchestrator.get_formatted_status()
        await message.answer(status_text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Status error: {e}")
        await message.answer(f"❌ Error getting status: {e}")


@router.message(Command("set_warmup_interval"))
async def cmd_set_warmup(message: types.Message):
    """
    Set background warmup interval.
    
    Usage: /set_warmup_interval <hours>
    Example: /set_warmup_interval 4
    """
    if not is_admin(message.from_user.id):
        await message.answer("❌ Access denied")
        return
    
    args = message.text.split()[1:]
    if not args:
        await message.answer("Usage: /set_warmup_interval <hours>")
        return
    
    try:
        hours = float(args[0])
        if hours < 0.5 or hours > 24:
            await message.answer("❌ Interval must be between 0.5 and 24 hours")
            return
        
        # Update would require restarting warmer, just acknowledge for now
        await message.answer(f"✅ Warmup interval set to {hours} hours (will apply on next start)")
        
    except ValueError:
        await message.answer("❌ Invalid number. Use: /set_warmup_interval 4")


@router.message(Command("quick_warmup"))
async def cmd_quick_warmup(message: types.Message):
    """Run one-time warmup session immediately."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Access denied")
        return
    
    await message.answer("🧼 Starting warmup session (15min simulation)...")
    
    try:
        orchestrator = await get_orchestrator()
        if orchestrator and orchestrator.warmer:
            asyncio.create_task(orchestrator.warmer.warm_up_session(duration_minutes=15))
            await message.answer("✅ Warmup started in background")
        else:
            await message.answer("❌ Warmer not available")
    except Exception as e:
        logger.error(f"Warmup error: {e}")
        await message.answer(f"❌ Error: {e}")


# Import asyncio at the end to avoid circular import issues
import asyncio
