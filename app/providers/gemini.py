"""
Google Gemini image generation client - genuinely free tier (50 requests/
day, no credit card) via Nano Banana 2, unlike OpenRouter's paid Images
API which returned 402 Payment Required without a funded balance.

Model ID note, checked live via search just before writing this:
gemini-3.1-flash-image-preview (the preview name) was deprecated and
shut down June 25, 2026 - already passed as of today. The stable/GA
successor is gemini-3.1-flash-image (no "-preview" suffix), confirmed
against Google's current model docs. If this 404s later, Google has
likely done another preview-to-GA rename - check ai.google.dev/gemini-api/
docs/models before assuming the code is wrong.

NOT verified against a live call from here (no network access in this
environment) - response shape (candidates[0].content.parts, looking for
inlineData.data as base64 PNG) is per Google's documented examples, but
untested end-to-end against a real key.
"""

import requests

from app.config import Config

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
DEFAULT_MODEL = "gemini-3.1-flash-image"


class GeminiClient:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or Config.GEMINI_API_KEY
        self.model = model or DEFAULT_MODEL

    def generate_image(self, prompt: str) -> str:
        """Returns a base64-encoded PNG string. telegram_client.send_photo
        already handles base64 strings (decodes and sends as bytes) - no
        changes needed there, this slots into the same image_client
        interface OpenRouterClient.generate_image() used before it."""
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is not set")

        url = GEMINI_URL.format(model=self.model)
        headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseModalities": ["IMAGE", "TEXT"]},
        }

        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()

        data = response.json()
        parts = data["candidates"][0]["content"]["parts"]

        for part in parts:
            if "inlineData" in part:
                return part["inlineData"]["data"]  # base64 string

        raise RuntimeError("Gemini response contained no image data")