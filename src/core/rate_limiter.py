"""
Adaptive Rate Limiter - Dynamic anti-ban protection for GRAMGPT.
Adjusts delays based on error streaks, flood waits, and action frequency.
"""

import logging
import random
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AdaptiveRateLimiter:
    """
    Smart rate limiting with adaptive delays.
    Learns from Telegram's flood errors and adjusts behavior dynamically.
    """
    
    # Base delay ranges (seconds) between different actions
    BASE_DELAYS = {
        "comment": (120, 300),      # 2-5 minutes between comments
        "reaction": (30, 90),       # 30-90 seconds between reactions
        "subscribe": (180, 600),    # 3-10 minutes between subscriptions
        "scroll": (2, 8),           # 2-8 seconds between scrolls
        "warmup_cycle": (600, 1800) # 10-30 minutes between warmup sessions
    }
    
    def __init__(self):
        self.actions_per_hour = 0
        self.last_flood_wait = 0
        self.error_streak = 0
        self.last_action_time = None
        self.hourly_reset_time = datetime.now()
        
        logger.info("⚡ AdaptiveRateLimiter initialized")
    
    def _reset_hourly_counter(self):
        """Reset hourly action counter if hour has passed."""
        now = datetime.now()
        if now - self.hourly_reset_time >= timedelta(hours=1):
            logger.info(f"⏰ Hourly counter reset: {self.actions_per_hour} actions in last hour")
            self.actions_per_hour = 0
            self.hourly_reset_time = now
            # Decrease error streak on successful hour
            if self.error_streak > 0:
                self.error_streak = max(0, self.error_streak - 1)
    
    async def get_delay(self, action_type: str = "comment") -> float:
        """
        Calculate dynamic delay based on current state.
        
        Formula:
        - Base delay from BASE_DELAYS
        - +50% if error_streak > 0
        - +30% if actions_per_hour > 15
        - +100% if last_flood_wait > 60 seconds
        
        Args:
            action_type: Type of action (comment, reaction, etc.)
        
        Returns:
            Delay in seconds
        """
        self._reset_hourly_counter()
        
        # Get base delay
        base_min, base_max = self.BASE_DELAYS.get(action_type, (60, 180))
        base_delay = random.uniform(base_min, base_max)
        
        # Apply multipliers
        multiplier = 1.0
        reasons = []
        
        if self.error_streak > 0:
            multiplier *= (1 + 0.5 * self.error_streak)
            reasons.append(f"error_streak={self.error_streak}")
        
        if self.actions_per_hour > 15:
            multiplier *= 1.3
            reasons.append(f"high_freq={self.actions_per_hour}/h")
        
        if self.last_flood_wait > 60:
            multiplier *= 1.5
            reasons.append(f"recent_flood={self.last_flood_wait}s")
        
        # Calculate final delay
        final_delay = base_delay * multiplier
        
        # Log the decision
        if reasons:
            logger.info(f"⚡ [rate] {action_type}: {final_delay:.1f}s (base: {base_delay:.1f}s, mult: {multiplier:.1f}x, reasons: {', '.join(reasons)})")
        else:
            logger.info(f"⚡ [rate] {action_type}: {final_delay:.1f}s (normal)")
        
        return final_delay
    
    def record_flood_wait(self, seconds: int) -> None:
        """
        Record a flood wait error from Telegram.
        
        Args:
            seconds: How long Telegram asked to wait
        """
        self.last_flood_wait = seconds
        self.error_streak += 1
        logger.warning(f"🚫 [rate] Flood wait recorded: {seconds}s (streak: {self.error_streak})")
    
    def record_success(self, action_type: str = "comment") -> None:
        """
        Record a successful action.
        
        Args:
            action_type: Type of action that succeeded
        """
        self.actions_per_hour += 1
        self.last_action_time = datetime.now()
        
        # Decrease error streak slowly on success
        if self.error_streak > 0 and random.random() > 0.7:
            self.error_streak -= 1
            logger.info(f"✅ [rate] Success recorded: {action_type} ({self.actions_per_hour}/h, streak recovering)")
        else:
            logger.info(f"✅ [rate] Success recorded: {action_type} ({self.actions_per_hour}/h)")
    
    def get_status(self) -> dict:
        """
        Get current rate limiter status.
        
        Returns:
            Dict with current stats
        """
        self._reset_hourly_counter()
        
        return {
            "actions_per_hour": self.actions_per_hour,
            "error_streak": self.error_streak,
            "last_flood_wait": self.last_flood_wait,
            "last_action": self.last_action_time.isoformat() if self.last_action_time else None,
            "status": "conservative" if self.error_streak > 0 or self.last_flood_wait > 60 else "normal"
        }
    
    def force_conservative_mode(self, duration_minutes: int = 60) -> None:
        """
        Force conservative mode after severe error.
        
        Args:
            duration_minutes: How long to stay conservative
        """
        self.error_streak += 2
        logger.warning(f"⚠️ [rate] Forced conservative mode for {duration_minutes}m")
    
    async def post_action_delay(self, action_type: str = "comment") -> None:
        """
        Convenience method: get delay and sleep.
        
        Args:
            action_type: Type of action to delay after
        """
        import asyncio
        delay = await self.get_delay(action_type)
        logger.info(f"⏳ [rate] Sleeping {delay:.1f}s after {action_type}")
        await asyncio.sleep(delay)
