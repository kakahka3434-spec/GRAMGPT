"""
Work Modes - Preset configurations for Reliable/Balanced/Aggressive operation.
Dynamic parameter adjustment based on risk tolerance.
"""

import logging
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ModeConfig:
    """Configuration for a work mode."""
    name: str
    comments_per_day: Tuple[int, int]
    delay_between_comments: Tuple[int, int]  # seconds (min, max)
    edit_delay: Tuple[int, int]  # seconds before editing emoji to promo
    warmup_intensity: str  # "low", "medium", "high"
    risk_tolerance: float  # 0-1
    flood_multiplier: float  # Delay multiplier after flood errors
    max_concurrent_channels: int  # How many channels to monitor
    cooldown_threshold: float  # Risk score to trigger auto-downgrade
    description: str


# Mode presets
MODES: Dict[str, ModeConfig] = {
    "reliable": ModeConfig(
        name="reliable",
        comments_per_day=(5, 10),
        delay_between_comments=(180, 600),  # 3-10 min
        edit_delay=(300, 600),  # 5-10 min
        warmup_intensity="high",
        risk_tolerance=0.2,
        flood_multiplier=2.0,
        max_concurrent_channels=5,
        cooldown_threshold=0.3,  # Downgrade if risk > 30%
        description="Maximum safety, minimal risk. Best for valuable accounts."
    ),
    
    "balanced": ModeConfig(
        name="balanced",
        comments_per_day=(15, 30),
        delay_between_comments=(60, 300),  # 1-5 min
        edit_delay=(180, 300),  # 3-5 min
        warmup_intensity="medium",
        risk_tolerance=0.5,
        flood_multiplier=1.5,
        max_concurrent_channels=10,
        cooldown_threshold=0.5,  # Downgrade if risk > 50%
        description="Good balance of volume and safety. Recommended default."
    ),
    
    "aggressive": ModeConfig(
        name="aggressive",
        comments_per_day=(40, 80),
        delay_between_comments=(30, 120),  # 30s-2min
        edit_delay=(60, 180),  # 1-3 min
        warmup_intensity="low",
        risk_tolerance=0.8,
        flood_multiplier=1.0,
        max_concurrent_channels=20,
        cooldown_threshold=0.7,  # Downgrade if risk > 70%
        description="High volume, higher risk. Use with caution."
    )
}

# Mode order for auto-downgrade
MODE_ORDER = ["aggressive", "balanced", "reliable"]


class WorkModeController:
    """
    Controls work mode selection and dynamic parameter adjustment.
    Handles auto-downgrade on risk detection.
    """
    
    def __init__(self, initial_mode: str = "balanced"):
        """
        Initialize mode controller.
        
        Args:
            initial_mode: Starting mode ('reliable', 'balanced', 'aggressive')
        """
        self.current_mode = initial_mode
        self.config = self._get_config(initial_mode)
        self.downgrade_history: list = []  # Track downgrades
        self._manual_override = False
        
        logger.info(f"🎮 WorkModeController initialized: {initial_mode}")
    
    def _get_config(self, mode: str) -> ModeConfig:
        """Get configuration for mode."""
        if mode not in MODES:
            logger.warning(f"⚠️ Unknown mode '{mode}', using 'balanced'")
            mode = "balanced"
        return MODES[mode]
    
    def switch_mode(self, new_mode: str, reason: str = "manual") -> bool:
        """
        Switch to a different work mode.
        
        Args:
            new_mode: Target mode
            reason: Why the switch happened
        
        Returns:
            True if switched successfully
        """
        if new_mode not in MODES:
            logger.error(f"❌ Invalid mode: {new_mode}")
            return False
        
        if new_mode == self.current_mode:
            return True
        
        old_mode = self.current_mode
        self.current_mode = new_mode
        self.config = self._get_config(new_mode)
        
        if reason == "risk_auto":
            self.downgrade_history.append({
                "from": old_mode,
                "to": new_mode,
                "at": __import__('datetime').datetime.now().isoformat(),
                "reason": "auto-downgrade"
            })
            logger.warning(f"🛡️ Auto-downgrade: {old_mode} → {new_mode}")
        else:
            self._manual_override = True
            logger.info(f"🎮 Mode switched: {old_mode} → {new_mode} ({reason})")
        
        return True
    
    def auto_downgrade(self, current_risk_score: float) -> bool:
        """
        Auto-downgrade mode if risk exceeds threshold.
        
        Args:
            current_risk_score: Current risk level (0-1)
        
        Returns:
            True if downgrade occurred
        """
        # Don't auto-downgrade if manually overridden
        if self._manual_override:
            return False
        
        # Check if we're already at lowest mode
        if self.current_mode == "reliable":
            return False
        
        # Check threshold
        if current_risk_score > self.config.cooldown_threshold:
            current_idx = MODE_ORDER.index(self.current_mode)
            new_mode = MODE_ORDER[current_idx + 1]  # Safer mode
            
            return self.switch_mode(new_mode, reason="risk_auto")
        
        return False
    
    def apply_to_rate_limiter(self, rate_limiter) -> None:
        """Apply current mode settings to rate limiter."""
        # Update base delays
        min_delay, max_delay = self.config.delay_between_comments
        rate_limiter.BASE_DELAYS["comment"] = (min_delay, max_delay)
        
        # Update flood multiplier
        rate_limiter.flood_multiplier = self.config.flood_multiplier
        
        logger.debug(f"🎮 Applied mode to rate limiter: delays {min_delay}-{max_delay}s")
    
    def apply_to_warmer(self, account_warmer) -> Dict[str, Any]:
        """
        Get warmup parameters for current mode.
        
        Returns:
            Dict with warmup settings
        """
        intensity_map = {
            "low": {
                "scroll_posts": (5, 10),
                "reactions_per_session": (1, 3),
                "subscriptions_per_day": (1, 2),
                "session_duration": (5, 10)
            },
            "medium": {
                "scroll_posts": (10, 20),
                "reactions_per_session": (3, 6),
                "subscriptions_per_day": (2, 4),
                "session_duration": (10, 20)
            },
            "high": {
                "scroll_posts": (20, 40),
                "reactions_per_session": (5, 10),
                "subscriptions_per_day": (3, 6),
                "session_duration": (20, 40)
            }
        }
        
        settings = intensity_map.get(self.config.warmup_intensity, intensity_map["medium"])
        logger.debug(f"🎮 Warmer settings ({self.config.warmup_intensity}): {settings}")
        
        return settings
    
    def apply_to_sniper(self, sniper) -> None:
        """Apply current mode settings to comment sniper."""
        min_edit, max_edit = self.config.edit_delay
        sniper.settings["edit_delay_min"] = min_edit
        sniper.settings["edit_delay_max"] = max_edit
        
        logger.debug(f"🎮 Applied mode to sniper: edit delay {min_edit}-{max_edit}s")
    
    def get_pipeline_settings(self) -> Dict[str, Any]:
        """Get all pipeline settings for current mode."""
        return {
            "mode": self.current_mode,
            "max_comments_per_hour": self.config.comments_per_day[1] // 24,
            "delay_range": self.config.delay_between_comments,
            "edit_delay_range": self.config.edit_delay,
            "max_channels": self.config.max_concurrent_channels,
            "risk_tolerance": self.config.risk_tolerance,
            "description": self.config.description
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current mode status."""
        return {
            "current_mode": self.current_mode,
            "description": self.config.description,
            "risk_tolerance": self.config.risk_tolerance,
            "max_comments_per_day": self.config.comments_per_day[1],
            "downgrades_count": len(self.downgrade_history),
            "auto_protection": not self._manual_override,
            "can_downgrade": self.current_mode != "reliable"
        }
    
    def get_formatted_status(self) -> str:
        """Get human-readable status."""
        status = self.get_status()
        
        emoji = "🐢" if status["current_mode"] == "reliable" else "🚶" if status["current_mode"] == "balanced" else "🚀"
        
        protection = "🛡️ Auto" if status["auto_protection"] else "⚠️ Manual"
        
        return f"""
{emoji} <b>Work Mode: {status['current_mode'].upper()}</b>

<b>Description:</b> {status['description']}

<b>Limits:</b>
• Comments/day: up to {status['max_comments_per_day']}
• Risk tolerance: {int(status['risk_tolerance']*100)}%

<b>Protection:</b> {protection}
<b>Auto-downgrades:</b> {status['downgrades_count']}
"""
    
    def reset_manual_override(self) -> None:
        """Reset manual override, allow auto-downgrades again."""
        self._manual_override = False
        logger.info("🎮 Manual override reset, auto-protection enabled")


# Mode transition helper
MODE_TRANSITIONS = {
    ("aggressive", "balanced"): "⚠️ Risk detected, switching to safer mode",
    ("balanced", "reliable"): "🛡️ High risk, switching to maximum safety",
    ("balanced", "aggressive"): "🚀 Manual upgrade to aggressive",
    ("reliable", "balanced"): "📈 Manual upgrade to balanced"
}
