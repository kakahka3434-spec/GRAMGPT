import hashlib
import random
import json
from typing import Dict

class FingerprintEngine:
    def __init__(self):
        self.devices = ["iPhone 15 Pro", "Samsung Galaxy S24", "Google Pixel 8", "Desktop Windows 11", "MacBook Pro M3"]
        self.browsers = ["Chrome/124.0.0.0", "Safari/17.4", "Firefox/125.0"]

    def generate_fingerprint(self, phone: str) -> Dict[str, str]:
        """Generates a unique hardware and software fingerprint for an account."""
        seed = hashlib.sha256(phone.encode()).hexdigest()
        random.seed(seed)

        device = random.choice(self.devices)
        browser = random.choice(self.browsers)
        screen_res = random.choice(["1920x1080", "1170x2532", "1440x3120"])

        return {
            "device": device,
            "user_agent": f"Mozilla/5.0 ({device}) AppleWebKit/537.36 (KHTML, like Gecko) {browser}",
            "screen": screen_res,
            "os_version": f"{random.randint(10, 15)}.0",
            "hardware_id": hashlib.md5(seed.encode()).hexdigest()
        }

    def generate_behavioral_dna(self) -> Dict[str, any]:
        """Generates unique behavioral patterns (DNA) for an account."""
        return {
            "preferred_hours": random.choice(["morning", "evening", "night", "work_hours"]),
            "typing_speed_wpm": random.randint(120, 200),
            "typo_frequency": random.uniform(0.01, 0.05),
            "interests": random.sample(["crypto", "marketing", "tech", "design", "lifestyle"], 2),
            "reaction_probability": random.uniform(0.3, 0.7)
        }

fp_engine = FingerprintEngine()
