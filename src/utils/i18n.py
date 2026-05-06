from typing import Dict

class I18nManager:
    def __init__(self, default_lang: str = "ru"):
        self.default_lang = default_lang
        self.translations = {
            "ru": {
                "welcome": "Добро пожаловать в GPTGRAM Ultimate",
                "settings": "Настройки",
                "active": "Активна"
            },
            "en": {
                "welcome": "Welcome to GPTGRAM Ultimate",
                "settings": "Settings",
                "active": "Active"
            }
        }

    def get(self, key: str, lang: str = None) -> str:
        lang = lang or self.default_lang
        return self.translations.get(lang, self.translations["en"]).get(key, key)

i18n = I18nManager()
