# app/utils/translator.py

"""
Translator Utility
------------------
Provides English ↔ Arabic translation using an external API.

score_service and report_service import:
    from app.utils.translator import Translator
"""

import httpx
from app.config.settings import settings


class Translator:
    """
    Wrapper class for async translation.
    Uses an external translation microservice.
    """

    def __init__(self, api_url: str | None = None):
        self.api_url = api_url or settings.TRANSLATION_API_URL
        self.client = None

    async def init(self):
        self.client = httpx.AsyncClient(timeout=30)

    async def close(self):
        await self.client.aclose()

    async def translate(self, text: str, target_lang: str = "en") -> str:
        """
        Translate text using the external API.

        Args:
            text (str): Input string.
            target_lang (str): "en" or "ar".

        Returns:
            str: Translated text.
        """

        if not text:
            return ""

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.api_url,
                json={"q": text,
                      "source": "ar",
                      "target": target_lang,
                      "format": "text"
                      }
            )
            response.raise_for_status()
            data = response.json()

        return data.get("translated_text", text)


# Global shared instance
translator = Translator()
