import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

class TelegramAccount:
    def __init__(self, phone: str, proxy: Optional[str] = None):
        self.phone = phone
        self.proxy = proxy
        self.status = "idle"
        self.risk_score = 0

class AccountManager:
    def __init__(self):
        self.accounts: List[TelegramAccount] = []

    def add_account(self, phone: str, proxy: Optional[str] = None):
        account = TelegramAccount(phone, proxy)
        self.accounts.append(account)
        logger.info(f"Added account {phone} with proxy {proxy}")

    def get_safe_account(self) -> Optional[TelegramAccount]:
        """Find an account with the lowest risk score."""
        if not self.accounts:
            return None
        return min(self.accounts, key=lambda a: a.risk_score)

    def rotate_proxies(self):
        """Logic to rotate proxies for accounts."""
        # Placeholder for complex rotation logic
        pass

account_manager = AccountManager()
