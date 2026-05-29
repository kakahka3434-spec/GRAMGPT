"""
Account Pool Manager - Multi-account rotation and status tracking for GRAMGPT.
Manages account lifecycle: active → cooldown → banned → warming.
"""

import asyncio
import logging
import json
import os
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from src.core.proxy_manager import ProxyManager

logger = logging.getLogger(__name__)


class AccountStatus(Enum):
    """Account lifecycle statuses."""
    ACTIVE = "active"
    COOLDOWN = "cooldown"
    BANNED = "banned"
    WARMING = "warming"
    ERROR = "error"


@dataclass
class Account:
    """Represents a single Telegram account in the pool."""
    phone: str
    session_path: str
    proxy: Optional[str] = None
    proxy_id: Optional[int] = None
    status: str = AccountStatus.WARMING.value
    added_at: str = ""
    last_used: Optional[str] = None
    cooldown_until: Optional[str] = None
    success_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None
    
    def __post_init__(self):
        if not self.added_at:
            self.added_at = datetime.now().isoformat()


class AccountPool:
    """
    Manages pool of Telegram accounts with round-robin rotation.
    Tracks status, handles cooldowns, provides health reports.
    """
    
    def __init__(self, settings: Optional[Dict] = None, pool_file: str = "data/account_pool.json"):
        """
        Initialize account pool.
        
        Args:
            settings: Optional configuration dict
            pool_file: JSON file to persist account list
        """
        self.settings = settings or {}
        self.pool_file = pool_file
        self.accounts: List[Account] = []
        self.current_index = 0
        self.proxy_manager = ProxyManager()
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(pool_file), exist_ok=True)
        
        # Load existing accounts
        self._load_pool()
        
        logger.info(f"🎯 AccountPool initialized ({len(self.accounts)} accounts)")
    
    def _load_pool(self) -> None:
        """Load accounts from JSON file."""
        if os.path.exists(self.pool_file):
            try:
                with open(self.pool_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.accounts = [Account(**acc) for acc in data.get('accounts', [])]
                    self.current_index = data.get('current_index', 0)
                logger.info(f"📂 Loaded {len(self.accounts)} accounts from {self.pool_file}")
            except Exception as e:
                logger.error(f"❌ Error loading pool: {e}")
                self.accounts = []
    
    def _save_pool(self) -> None:
        """Save accounts to JSON file."""
        try:
            data = {
                'accounts': [asdict(acc) for acc in self.accounts],
                'current_index': self.current_index,
                'saved_at': datetime.now().isoformat()
            }
            with open(self.pool_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"❌ Error saving pool: {e}")
    
    def add_account(
        self,
        phone: str,
        session_path: str,
        proxy_id: Optional[int] = None,
        validate_proxy: bool = True
    ) -> bool:
        """
        Add new account to pool.
        
        Args:
            phone: Phone number with country code
            session_path: Path to Telethon session file
            proxy_id: Optional proxy ID from the proxies pool
            validate_proxy: Whether to validate proxy before adding
        
        Returns:
            True if added successfully
        """
        if any(acc.phone == phone for acc in self.accounts):
            logger.warning(f"⚠️ Account {phone} already in pool")
            return False

        proxy_url = None
        if proxy_id is not None:
            import sqlite3
            try:
                conn = sqlite3.connect("gramgpt.db")
                row = conn.execute("SELECT url FROM proxies WHERE id=? AND is_active=1", (proxy_id,)).fetchone()
                if row:
                    proxy_url = row[0]
                conn.close()
            except Exception as e:
                logger.warning(f"Could not resolve proxy_id {proxy_id}: {e}")

        account = Account(
            phone=phone,
            session_path=session_path,
            proxy_id=proxy_id,
            proxy=proxy_url,
            status=AccountStatus.WARMING.value
        )

        self.accounts.append(account)
        self._save_pool()

        logger.info(f"✅ Added account {phone} (proxy_id={proxy_id}, proxy={proxy_url or 'none'})")
        return True
    
    def remove_account(self, phone: str) -> bool:
        """Remove account from pool by phone number."""
        original_count = len(self.accounts)
        self.accounts = [acc for acc in self.accounts if acc.phone != phone]
        
        if len(self.accounts) < original_count:
            self._save_pool()
            logger.info(f"✅ Removed account {phone}")
            return True
        
        logger.warning(f"⚠️ Account {phone} not found in pool")
        return False
    
    def get_next_active(self, skip_cooldown_check: bool = False) -> Optional[Account]:
        """
        Get next active account using round-robin.
        
        Args:
            skip_cooldown_check: If True, ignore cooldown status
        
        Returns:
            Active Account or None if all on cooldown/banned
        """
        if not self.accounts:
            logger.warning("🎯 Empty account pool")
            return None
        
        # Check and clear expired cooldowns
        self._update_cooldowns()
        
        # Find next active account
        attempts = 0
        original_index = self.current_index
        
        while attempts < len(self.accounts):
            account = self.accounts[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.accounts)
            
            # Check if account is usable
            if account.status in [AccountStatus.ACTIVE.value, AccountStatus.WARMING.value]:
                if skip_cooldown_check or not account.cooldown_until:
                    account.last_used = datetime.now().isoformat()
                    self._save_pool()
                    logger.info(f"🎯 Selected account: {account.phone} ({account.status})")
                    return account
            
            attempts += 1
        
        # All accounts on cooldown/banned
        logger.warning(f"🚫 No active accounts available ({len(self.accounts)} total, all on cooldown/banned)")
        
        # If skip_cooldown_check is False, try again with it enabled
        if not skip_cooldown_check:
            logger.info("🔄 Retrying with cooldown bypass...")
            return self.get_next_active(skip_cooldown_check=True)
        
        return None
    
    def _update_cooldowns(self) -> None:
        """Clear expired cooldowns and update statuses."""
        now = datetime.now()
        updated = False
        
        for account in self.accounts:
            if account.cooldown_until:
                cooldown_time = datetime.fromisoformat(account.cooldown_until)
                if now >= cooldown_time:
                    account.cooldown_until = None
                    account.status = AccountStatus.ACTIVE.value
                    updated = True
                    logger.info(f"⏰ Account {account.phone} cooldown expired, now active")
        
        if updated:
            self._save_pool()
    
    def mark_status(
        self,
        phone: str,
        status: AccountStatus,
        cooldown_minutes: int = 0,
        error_message: Optional[str] = None
    ) -> bool:
        """
        Change account status with optional cooldown.
        
        Args:
            phone: Account phone number
            status: New status
            cooldown_minutes: If > 0, set cooldown until N minutes from now
            error_message: Optional error description
        
        Returns:
            True if status changed
        """
        for account in self.accounts:
            if account.phone == phone:
                old_status = account.status
                account.status = status.value
                
                # Set cooldown if specified
                if cooldown_minutes > 0:
                    cooldown_until = datetime.now() + timedelta(minutes=cooldown_minutes)
                    account.cooldown_until = cooldown_until.isoformat()
                
                # Track errors
                if error_message:
                    account.last_error = error_message
                    account.error_count += 1
                
                # Track success
                if status == AccountStatus.ACTIVE:
                    account.success_count += 1
                
                self._save_pool()
                
                logger.info(
                    f"🏷️ Account {phone}: {old_status} → {status.value}"
                    + (f" (cooldown: {cooldown_minutes}min)" if cooldown_minutes else "")
                )
                return True
        
        logger.warning(f"⚠️ Account {phone} not found for status update")
        return False
    
    def record_success(self, phone: str) -> None:
        """Record successful action for account."""
        for account in self.accounts:
            if account.phone == phone:
                account.success_count += 1
                account.last_error = None
                self._save_pool()
                break
    
    def record_error(self, phone: str, error: str, cooldown_minutes: int = 0) -> None:
        """Record error and optionally set cooldown."""
        for account in self.accounts:
            if account.phone == phone:
                account.error_count += 1
                account.last_error = error
                
                if cooldown_minutes > 0:
                    cooldown_until = datetime.now() + timedelta(minutes=cooldown_minutes)
                    account.cooldown_until = cooldown_until.isoformat()
                    account.status = AccountStatus.COOLDOWN.value
                
                self._save_pool()
                logger.warning(f"⚠️ Account {phone} error: {error}")
                break
    
    def get_health_report(self) -> Dict[str, Any]:
        """
        Get comprehensive pool health report.
        
        Returns:
            Dict with pool statistics
        """
        self._update_cooldowns()
        
        total = len(self.accounts)
        active = sum(1 for acc in self.accounts if acc.status == AccountStatus.ACTIVE.value)
        warming = sum(1 for acc in self.accounts if acc.status == AccountStatus.WARMING.value)
        cooldown = sum(1 for acc in self.accounts if acc.status == AccountStatus.COOLDOWN.value)
        banned = sum(1 for acc in self.accounts if acc.status == AccountStatus.BANNED.value)
        error = sum(1 for acc in self.accounts if acc.status == AccountStatus.ERROR.value)
        
        # Calculate success rate
        total_success = sum(acc.success_count for acc in self.accounts)
        total_errors = sum(acc.error_count for acc in self.accounts)
        total_actions = total_success + total_errors
        
        success_rate = (total_success / total_actions * 100) if total_actions > 0 else 0
        
        # Risk score (0-100)
        # Higher = more risky (cooldowns, errors, low success rate)
        risk_score = 0
        if total > 0:
            risk_score += (cooldown / total) * 30  # 30% weight for cooldowns
            risk_score += (banned / total) * 50      # 50% weight for bans
            risk_score += (100 - success_rate) * 0.2  # 20% weight for success rate
        
        return {
            "total": total,
            "active": active,
            "warming": warming,
            "cooldown": cooldown,
            "banned": banned,
            "error": error,
            "success_rate": round(success_rate, 1),
            "total_actions": total_actions,
            "total_success": total_success,
            "total_errors": total_errors,
            "risk_score": round(risk_score, 1),
            "risk_level": "high" if risk_score > 50 else "medium" if risk_score > 25 else "low",
            "proxy_coverage": sum(1 for acc in self.accounts if acc.proxy) / total * 100 if total > 0 else 0
        }
    
    def get_formatted_report(self) -> str:
        """Get human-readable health report."""
        report = self.get_health_report()
        
        emoji = "🟢" if report["risk_level"] == "low" else "🟡" if report["risk_level"] == "medium" else "🔴"
        
        text = f"""
{emoji} <b>Pool Health Report</b>

<b>Accounts:</b> {report['total']} total
• 🟢 Active: {report['active']}
• 🟡 Warming: {report['warming']}
• ⏰ Cooldown: {report['cooldown']}
• 🔴 Banned: {report['banned']}
• ⚠️ Error: {report['error']}

<b>Performance:</b>
• Success rate: {report['success_rate']}%
• Total actions: {report['total_actions']}
• Proxy coverage: {round(report['proxy_coverage'], 1)}%

<b>Risk:</b> {report['risk_score']}/100 ({report['risk_level']})
"""
        return text
    
    def get_available_proxies(self) -> List[Dict]:
        """Fetch proxies from SQLite pool for dropdown selection."""
        try:
            db_path = "gramgpt.db"
            if os.path.exists(db_path):
                import sqlite3
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    "SELECT id, url, type, host, port, is_active, ping_ms, country FROM proxies WHERE is_active=1 ORDER BY ping_ms ASC"
                ).fetchall()
                conn.close()
                return [dict(r) for r in rows]
        except Exception as e:
            logger.warning(f"Could not load proxies: {e}")
        return []

    def update_account_proxy(self, phone: str, proxy_id: Optional[int] = None) -> bool:
        """Change proxy assigned to an account. proxy_id=None means no proxy."""
        for acc in self.accounts:
            if acc.phone == phone:
                acc.proxy_id = proxy_id
                if proxy_id is not None:
                    proxies = self.get_available_proxies()
                    match = next((p for p in proxies if p["id"] == proxy_id), None)
                    acc.proxy = match["url"] if match else None
                else:
                    acc.proxy = None
                self._save_pool()
                logger.info(f"🔌 Account {phone} proxy changed to {acc.proxy or 'none'}")
                return True
        return False

    def list_accounts(self) -> List[Dict]:
        """Return list of all accounts as dicts."""
        self._update_cooldowns()
        result = []
        for acc in self.accounts:
            d = asdict(acc)
            # Enrich with proxy info from proxy_id
            if acc.proxy_id:
                import sqlite3
                try:
                    conn = sqlite3.connect("gramgpt.db")
                    row = conn.execute("SELECT url, ping_ms, is_active FROM proxies WHERE id=?", (acc.proxy_id,)).fetchone()
                    if row:
                        d["proxy_url"] = row[0]
                        d["proxy_ping"] = row[1]
                        d["proxy_active"] = bool(row[2])
                    conn.close()
                except Exception:
                    pass
            result.append(d)
        return result
