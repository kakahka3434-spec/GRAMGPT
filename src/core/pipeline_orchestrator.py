"""
Pipeline Orchestrator - Main automation controller for GRAMGPT.
Advanced promo workflow: Discovery → Sniper → Edit → Analytics.
"""

import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from src.services.telegram_user_client import TelegramUserClient
from src.services.comment_sender import CommentSender
from src.services.account_warmer import AccountWarmer
from src.services.channel_discovery import ChannelDiscovery
from src.services.comment_sniper import CommentSniper
from src.services.promo_engine import PromoEngine
from src.core.rate_limiter import AdaptiveRateLimiter
from src.core.work_modes import WorkModeController
from src.db.comment_memory import comment_memory

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """
    Advanced automation pipeline with graceful shutdown and real-time stats.
    """
    
    def __init__(
        self,
        telegram_client: TelegramUserClient,
        comment_sender: CommentSender,
        account_warmer: Optional[AccountWarmer] = None,
        settings: Optional[Dict] = None
    ):
        """
        Initialize pipeline orchestrator.
        
        Args:
            telegram_client: Connected TelegramUserClient
            comment_sender: Initialized CommentSender
            account_warmer: Optional AccountWarmer for background warming
            settings: Pipeline configuration
        """
        self.telegram = telegram_client
        self.comment_sender = comment_sender
        self.warmer = account_warmer
        self.settings = settings or {}
        
        # Rate limiter
        self.rate_limiter = AdaptiveRateLimiter()
        
        # Work mode controller (NEW)
        self.mode_controller = WorkModeController(
            initial_mode=settings.get("work_mode", "balanced") if settings else "balanced"
        )
        
        # Channel discovery (NEW)
        self.discovery = ChannelDiscovery(telegram_client)
        
        # Promo engine (NEW)
        self.promo_engine = PromoEngine(settings)
        
        # Comment sniper (NEW) - initialized in start()
        self.sniper: Optional[CommentSniper] = None
        
        # State
        self.is_running = False
        self._stop_requested = False
        self._current_task = None
        self._warmup_task = None
        self._mode_check_task: Optional[asyncio.Task] = None
        
        # Stats
        self.stats = {
            "comments_total": 0,
            "comments_this_hour": 0,
            "errors_total": 0,
            "started_at": None,
            "last_comment_at": None,
            "last_error": None,
            "current_channel": None,
            "auto_downgrades": 0,
            "posts_seen": 0
        }
        
        # Hourly counter reset
        self._hourly_reset_time = datetime.now()
        
        logger.info("🔄 PipelineOrchestrator initialized (v2 - Promo Workflow)")
    
    def _reset_hourly_stats(self):
        """Reset hourly comment counter."""
        now = datetime.now()
        if now - self._hourly_reset_time >= timedelta(hours=1):
            logger.info(f"📊 Hourly stats reset: {self.stats['comments_this_hour']} comments")
            self.stats["comments_this_hour"] = 0
            self._hourly_reset_time = now
    
    async def start(
        self,
        target_channels: List[str],
        style: str = "balanced",
        max_comments_per_hour: int = 10,
        use_sniper: bool = False,
        target_link: str = "",
        keywords: Optional[List[str]] = None
    ) -> None:
        """
        Start the automation pipeline.
        
        Args:
            target_channels: List of channel usernames to monitor
            style: Comment style (expert, engaging, casual, balanced)
            max_comments_per_hour: Safety limit
            use_sniper: If True, use CommentSniper (emoji → edit) instead of regular comments
            target_link: Link to promote (for sniper mode)
            keywords: Keywords for channel discovery (if no target_channels provided)
        """
        if self.is_running:
            logger.warning("🔄 Pipeline already running!")
            return
        
        if not self.telegram._is_connected:
            logger.error("❌ Telegram client not connected!")
            return
        
        self.is_running = True
        self._stop_requested = False
        self.stats["started_at"] = datetime.now()
        self.stats["current_channel"] = None
        
        # Apply work mode to all components
        self._apply_work_mode()
        
        # Auto-discover channels if keywords provided and no channels
        if not target_channels and keywords:
            logger.info(f"🔍 Auto-discovering channels for keywords: {keywords}")
            discovered = await self.discovery.discover_target_channels(
                keywords=keywords,
                min_members=1000,
                max_results=self.mode_controller.config.max_concurrent_channels
            )
            target_channels = [c["username"] for c in discovered]
            logger.info(f"🎯 Discovered {len(target_channels)} channels")
        
        logger.info(f"🚀 Pipeline STARTED")
        logger.info(f"   Mode: {self.mode_controller.current_mode}")
        logger.info(f"   Channels: {', '.join(target_channels) if target_channels else 'None'}")
        logger.info(f"   Style: {style}")
        logger.info(f"   Sniper mode: {use_sniper}")
        
        # Initialize and start sniper if requested
        if use_sniper and target_channels:
            self.sniper = CommentSniper(
                telegram_client=self.telegram,
                promo_engine=self.promo_engine,
                settings={"target_link": target_link}
            )
            
            # Apply mode settings to sniper
            self.mode_controller.apply_to_sniper(self.sniper)
            
            # Start monitoring
            await self.sniper.start_monitoring(
                channels=target_channels,
                target_link=target_link
            )
        
        # Start background warmup if available
        if self.warmer:
            warmup_settings = self.mode_controller.apply_to_warmer(self.warmer)
            self._warmup_task = asyncio.create_task(
                self.warmer.run_background_warmup(interval_hours=4.0)
            )
        
        # Start risk monitoring for auto-downgrade
        self._mode_check_task = asyncio.create_task(self._risk_monitor_loop())
        
        # Run main loop (or just wait if in sniper mode)
        try:
            if use_sniper:
                # In sniper mode, just keep alive and monitor
                await self._run_sniper_loop(target_channels)
            else:
                await self._run_loop(target_channels, style, max_comments_per_hour)
        except asyncio.CancelledError:
            logger.info("🛑 Pipeline cancelled")
        except Exception as e:
            logger.error(f"💥 Pipeline error: {e}")
        finally:
            await self._cleanup()
    
    def _apply_work_mode(self) -> None:
        """Apply current work mode to all components."""
        # Apply to rate limiter
        self.mode_controller.apply_to_rate_limiter(self.rate_limiter)
        
        logger.info(f"🎮 Applied work mode: {self.mode_controller.current_mode}")
        logger.info(f"   Comments/day: {self.mode_controller.config.comments_per_day}")
        logger.info(f"   Delay range: {self.mode_controller.config.delay_between_comments}")
    
    async def _risk_monitor_loop(self) -> None:
        """Background loop for risk monitoring and auto-downgrade."""
        logger.info("🛡️ Risk monitor started")
        
        while self.is_running and not self._stop_requested:
            try:
                # Calculate current risk from various factors
                risk_score = self._calculate_current_risk()
                
                # Check for auto-downgrade
                if self.mode_controller.auto_downgrade(risk_score):
                    self.stats["auto_downgrades"] += 1
                    logger.warning(f"🛡️ Auto-downgrade triggered! Risk: {risk_score:.2f}")
                    
                    # Re-apply new mode settings
                    self._apply_work_mode()
                    if self.sniper:
                        self.mode_controller.apply_to_sniper(self.sniper)
                
                # Wait before next check
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Risk monitor error: {e}")
                await asyncio.sleep(30)
        
        logger.info("🛡️ Risk monitor stopped")
    
    def _calculate_current_risk(self) -> float:
        """Calculate current risk score based on pipeline stats."""
        risk = 0.0
        
        # Factor 1: Error rate (0-0.4 weight)
        if self.stats["errors_total"] > 0:
            error_rate = self.stats["errors_total"] / max(self.stats["comments_total"], 1)
            risk += min(error_rate * 2, 0.4)
        
        # Factor 2: Rate limiter status (0-0.3 weight)
        if self.rate_limiter.error_streak > 2:
            risk += min(self.rate_limiter.error_streak * 0.1, 0.3)
        
        # Factor 3: High hourly activity (0-0.3 weight)
        max_per_hour = self.mode_controller.config.comments_per_day[1] / 24
        if self.stats["comments_this_hour"] > max_per_hour * 0.8:
            risk += 0.2
        
        return min(risk, 1.0)
    
    async def _run_sniper_loop(self, channels: List[str]) -> None:
        """Keep-alive loop for sniper mode."""
        logger.info("🎯 Sniper loop started - monitoring for new posts")
        
        while self.is_running and not self._stop_requested:
            try:
                # Update stats from sniper
                if self.sniper:
                    sniper_stats = self.sniper.get_status()
                    self.stats["posts_seen"] = sniper_stats.get("posts_seen", 0)
                    self.stats["comments_total"] = sniper_stats.get("emoji_sent", 0)
                    self.stats["errors_total"] = sniper_stats.get("edits_failed", 0)
                
                # Just wait - sniper runs in background
                await asyncio.sleep(10)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Sniper loop error: {e}")
                await asyncio.sleep(5)
    
    async def _run_loop(
        self,
        channels: List[str],
        style: str,
        max_per_hour: int
    ) -> None:
        """
        Main pipeline loop.
        
        Cycle:
        1. Pick random channel
        2. Parse recent posts
        3. Filter already commented (memory)
        4. Generate and send comment
        5. Apply dynamic delay
        6. Repeat (unless stop requested)
        """
        while self.is_running and not self._stop_requested:
            try:
                self._reset_hourly_stats()
                
                # Check hourly limit
                if self.stats["comments_this_hour"] >= max_per_hour:
                    logger.info(f"⏸️ Hourly limit reached ({max_per_hour}), pausing...")
                    await asyncio.sleep(300)  # Wait 5 minutes
                    continue
                
                # Step 1: Select random channel
                channel = random.choice(channels)
                self.stats["current_channel"] = channel
                
                logger.info(f"🔄 [pipeline] Processing @{channel}")
                
                # Step 2: Parse recent posts (last 5)
                posts = await self.telegram.parse_last_messages(channel, limit=5)
                
                if not posts:
                    logger.warning(f"🔄 [pipeline] No posts found in @{channel}")
                    await self._apply_delay("empty_channel")
                    continue
                
                # Step 3: Find un-commented posts
                new_posts = []
                for post in posts:
                    if not comment_memory.is_already_commented(channel, post["id"], hours=24):
                        new_posts.append(post)
                
                if not new_posts:
                    logger.info(f"🔄 [pipeline] All recent posts already commented in @{channel}")
                    await self._apply_delay("all_commented")
                    continue
                
                logger.info(f"🔄 [pipeline] Found {len(new_posts)} new posts to comment")
                
                # Step 4: Comment on first available post
                target_post = new_posts[0]
                
                logger.info(f"🎯 [pipeline] Commenting on post {target_post['id']}")
                
                result = await self.comment_sender.comment_with_full_cycle(
                    channel=channel,
                    post_id=target_post["id"],
                    post_text=target_post.get("text", ""),
                    style=style
                )
                
                if result:
                    # Success
                    self.stats["comments_total"] += 1
                    self.stats["comments_this_hour"] += 1
                    self.stats["last_comment_at"] = datetime.now()
                    
                    self.rate_limiter.record_success("comment")
                    
                    logger.info(f"✅ [cycle] Comment {self.stats['comments_total']} sent successfully")
                    
                    # Apply post-comment delay
                    await self._apply_delay("after_comment")
                else:
                    # Failed (but not error - maybe already commented or no discussion)
                    logger.warning(f"⚠️ [cycle] Comment skipped (no discussion group or duplicate)")
                    await self._apply_delay("skipped")
                
            except asyncio.CancelledError:
                logger.info("🛑 [pipeline] Loop cancelled")
                break
            except Exception as e:
                logger.error(f"❌ [pipeline] Loop error: {e}")
                self.stats["errors_total"] += 1
                self.stats["last_error"] = str(e)
                self.rate_limiter.record_flood_wait(30)  # Assume conservative
                await self._apply_delay("error")
    
    async def _apply_delay(self, reason: str) -> None:
        """Apply appropriate delay based on reason."""
        delays = {
            "after_comment": (120, 300),      # 2-5 min after success
            "empty_channel": (60, 120),        # 1-2 min if no posts
            "all_commented": (180, 600),       # 3-10 min if all done
            "skipped": (60, 180),             # 1-3 min if skipped
            "error": (300, 600)               # 5-10 min after error
        }
        
        min_s, max_s = delays.get(reason, (60, 180))
        delay = random.uniform(min_s, max_s)
        
        # Apply rate limiter multiplier
        multiplier = 1.0
        if self.rate_limiter.error_streak > 0:
            multiplier = 1 + (0.3 * self.rate_limiter.error_streak)
        
        final_delay = delay * multiplier
        
        logger.info(f"⏳ [delay] {reason}: sleeping {final_delay:.0f}s (base: {delay:.0f}s, mult: {multiplier:.1f}x)")
        
        # Check for stop request during sleep
        for _ in range(int(final_delay)):
            if self._stop_requested:
                break
            await asyncio.sleep(1)
    
    async def stop(self) -> None:
        """
        Graceful shutdown.
        Waits for current operation to complete, saves state.
        """
        if not self.is_running:
            logger.info("🛑 Pipeline not running")
            return
        
        logger.info("🛑 STOP requested - graceful shutdown...")
        self._stop_requested = True
        self.is_running = False
        
        # Cancel all tasks
        tasks = [self._warmup_task, self._mode_check_task]
        for task in tasks:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Stop sniper
        if self.sniper:
            await self.sniper.stop_monitoring()
        
        logger.info("🛑 Pipeline stopped gracefully")
        logger.info(f"📊 Final stats: {self.stats['comments_total']} comments, {self.stats['errors_total']} errors, {self.stats['auto_downgrades']} downgrades")
    
    async def _cleanup(self) -> None:
        """Cleanup resources."""
        self.is_running = False
        
        # Stop warmer
        if self.warmer:
            await self.warmer.stop()
        
        # Stop sniper
        if self.sniper:
            await self.sniper.stop_monitoring()
        
        # Cancel tasks
        if self._mode_check_task:
            self._mode_check_task.cancel()
        
        logger.info("🧹 Pipeline cleanup completed")
    
    def get_status(self) -> Dict[str, any]:
        """
        Get current pipeline status.
        
        Returns:
            Status dict with all metrics
        """
        self._reset_hourly_stats()
        
        uptime = None
        if self.stats["started_at"]:
            uptime_seconds = (datetime.now() - self.stats["started_at"]).total_seconds()
            uptime = f"{int(uptime_seconds // 3600)}h {int((uptime_seconds % 3600) // 60)}m"
        
        # Get mode status
        mode_status = self.mode_controller.get_status()
        
        # Get sniper status if active
        sniper_status = None
        if self.sniper:
            sniper_status = self.sniper.get_status()
        
        return {
            "running": self.is_running,
            "uptime": uptime,
            "work_mode": mode_status,
            "sniper": sniper_status,
            "comments_total": self.stats["comments_total"],
            "comments_this_hour": self.stats["comments_this_hour"],
            "errors_total": self.stats["errors_total"],
            "auto_downgrades": self.stats["auto_downgrades"],
            "posts_seen": self.stats["posts_seen"],
            "last_comment": self.stats["last_comment_at"].strftime("%H:%M:%S") if self.stats["last_comment_at"] else None,
            "last_error": self.stats["last_error"],
            "current_channel": self.stats["current_channel"],
            "rate_limiter": self.rate_limiter.get_status()
        }
    
    def get_formatted_status(self) -> str:
        """Get human-readable status string."""
        status = self.get_status()
        
        emoji = "🟢" if status["running"] else "🔴"
        
        # Mode emoji
        mode_name = status["work_mode"]["current_mode"]
        mode_emoji = "🐢" if mode_name == "reliable" else "🚶" if mode_name == "balanced" else "🚀"
        
        # Sniper status
        sniper_info = ""
        if status["sniper"]:
            sniper = status["sniper"]
            sniper_emoji = "🎯" if sniper["monitoring"] else "⏹️"
            sniper_info = f"""
<b>{sniper_emoji} Sniper:</b>
• Posts seen: {sniper["posts_seen"]}
• Emoji sent: {sniper["emoji_sent"]}
• Edits done: {sniper["edits_completed"]}
• Pending: {sniper["pending_edits"]}

"""
        
        text = f"""
{emoji} <b>Pipeline Status</b>

{mode_emoji} <b>Mode: {mode_name.upper()}</b>
<b>State:</b> {"Running" if status["running"] else "Stopped"}
<b>Uptime:</b> {status["uptime"] or "N/A"}
<b>Auto-downgrades:</b> {status["auto_downgrades"]}

<b>Activity:</b>
• Comments: {status["comments_total"]} (this hour: {status["comments_this_hour"]})
• Posts seen: {status["posts_seen"]}
• Errors: {status["errors_total"]}

{sniper_info}<b>Rate Limiter:</b>
• Actions/hour: {status["rate_limiter"]["actions_per_hour"]}
• Error streak: {status["rate_limiter"]["error_streak"]}
• Status: {status["rate_limiter"]["status"]}
"""
        return text
    
    def switch_mode(self, new_mode: str) -> bool:
        """
        Manually switch work mode.
        
        Args:
            new_mode: Target mode (reliable, balanced, aggressive)
        
        Returns:
            True if switched
        """
        success = self.mode_controller.switch_mode(new_mode, reason="manual")
        if success:
            self._apply_work_mode()
            if self.sniper:
                self.mode_controller.apply_to_sniper(self.sniper)
        return success
