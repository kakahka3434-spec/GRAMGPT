import logging
from src.db.database import db

logger = logging.getLogger(__name__)

class ReferralSystem:
    def generate_referral_link(self, user_id: int) -> str:
        """Generates a deep link for the bot."""
        return f"https://t.me/gptgram_bot?start=ref_{user_id}"

    async def process_new_user(self, user_id: int, start_command: str):
        """Processes a new user who joined via a referral link."""
        if start_command.startswith("ref_"):
            try:
                referrer_id = int(start_command.split("_")[1])
                if user_id != referrer_id:
                    db.add_referral(user_id, referrer_id)
                    logger.info(f"User {user_id} referred by {referrer_id}")
                    # In real prod, we would add +20% limits here
                    return referrer_id
            except (ValueError, IndexError):
                pass
        return None

referral_system = ReferralSystem()
