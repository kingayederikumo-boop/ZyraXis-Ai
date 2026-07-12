"""
OpenRouter client - chat, image generation, web-search-grounded chat,
file analysis, and video generation.

Confirmed against OpenRouter's current docs (checked live, July 2026):
- Chat: POST /api/v1/chat/completions (unchanged, was already correct)
- Image generation: dedicated POST /api/v1/images endpoint
- Web search: openrouter:web_search server tool, not the deprecated
  :online/plugins approach
- Fallback routing: top-level `models` array + `route: "fallback"`
- PDF/file input: `file` content type in chat/completions, base64 data URL
  for private files (Telegram files aren't public), `file-parser` plugin
  with `mistral-ocr` engine for scanned/complex PDFs
- Video generation: genuinely async - POST /api/v1/videos returns a job id
  and polling_url immediately (generation itself takes 30s to minutes, per
  OpenRouter's own docs). GET the polling_url for status. On "completed",
  unsigned_urls[0] is the download link - these point back at the OpenRouter
  API and need the bearer token, they are NOT public URLs despite the name.

NOT verified against a live call from here (no network access in this
environment) - the /api/v1/images response shape (see generate_image
docstring), and the exact PDF file-parser response shape (assumed it
behaves like a normal chat completion with parsed content substituted in -
documented behavior, but untested end-to-end with a real key).

Each client instance takes its own api_key, so different features can use
different OpenRouter keys (for per-feature spend limits on OpenRouter's
dashboard) without any code change - see app/core/engine.py.
"""

import base64
import requests

from app.config import Config

CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"
IMAGE_URL = "https://openrouter.ai/api/v1/images"
VIDEO_URL = "https://openrouter.ai/api/v1/videos"

DEFAULT_CHAT_MODEL = "openai/gpt-4o-mini"
DEFAULT_IMAGE_MODEL = "google/gemini-2.5-flash-image"
DEFAULT_VIDEO_MODEL = "google/veo-3.1"

# Extensions read as plain text and inlined directly into the prompt -
# simpler and cheaper than routing through the file/PDF pipeline, and
# these formats don't need OCR or layout parsing.
TEXT_EXTENSIONS = {
    ".txt", ".md", ".csv", ".json", ".py", ".js", ".ts", ".java",
    ".c", ".cpp", ".html", ".css", ".yaml", ".yml", ".xml",
}

# Cap on inlined text - a very large file would blow context and cost.
# Truncated, not rejected, so the user still gets something useful.
MAX_TEXT_CHARS = 30000

FILE_ANALYSIS_SYSTEM_PROMPT = (
    "You are ZyraXis's file analysis assistant. Summarize, explain, or "
    "answer questions about the provided document precisely. Quote exact "
    "figures/dates when present rather than paraphrasing them."
)


class OpenRouterClient:
    def __init__(self, model: str | None = None, api_key: str | None = None, use_fallback: bool = False):
        self.model = model or DEFAULT_CHAT_MODEL
        self.api_key = api_key or Config.OPENROUTER_API_KEY
        self.use_fallback = use_fallback

    def _headers(self):
        if not self.api_key:
            raise RuntimeError("No OpenRouter API key set for this client")
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _routing(self) -> dict:
        """Fallback chain, opt-in per client. Chat/roleplay/code use it by
        default (higher value from staying up); search/image don't unless
        explicitly enabled, since their model lists aren't interchangeable
        in the same way."""
        if not self.use_fallback:
            return {}
        return {"models": Config.OPENROUTER_MODEL_CHAIN, "route": "fallback"}

    def chat(self, text: str, system: str | None = None) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": text})

        payload = {"model": self.model, "messages": messages, **self._routing()}

        response = requests.post(CHAT_URL, headers=self._headers(), json=payload, timeout=30)
        response.raise_for_status()

        data = response.json()
        return data["choices"][0]["message"]["content"]

    def search(self, text: str) -> str:
        """Web-search-grounded chat, using OpenRouter's current recommended
        approach (server tool), not the deprecated :online suffix."""
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": text}],
            "tools": [{"type": "openrouter:web_search"}],
            **self._routing(),
        }

        response = requests.post(CHAT_URL, headers=self._headers(), json=payload, timeout=45)
        response.raise_for_status()

        data = response.json()
        return data["choices"][0]["message"]["content"]

    def generate_image(self, prompt: str, model: str | None = None) -> str:
        """Returns an image URL. See module docstring - response shape is
        unverified against a live call."""
        payload = {
            "model": model or DEFAULT_IMAGE_MODEL,
            "prompt": prompt,
        }

        response = requests.post(IMAGE_URL, headers=self._headers(), json=payload, timeout=60)
        response.raise_for_status()

        data = response.json()
        image_data = data["data"][0]
        return image_data.get("url") or image_data.get("b64_json")

    def analyze_file(self, file_bytes: bytes, filename: str, prompt: str) -> str:
        """Routes by extension: plain text formats are inlined directly
        (cheap, simple, no OCR needed); .pdf goes through OpenRouter's
        file-parser plugin; .docx is extracted locally via python-docx
        first (OpenRouter's documented file pipeline is PDF-specific, not
        a generic office-document parser) then treated as text. Anything
        else raises - guessing at a binary format's content would be worse
        than admitting it's unsupported."""
        ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        if ext in TEXT_EXTENSIONS:
            text = file_bytes.decode("utf-8", errors="replace")[:MAX_TEXT_CHARS]
            return self.chat(f"{prompt}\n\n---\n{text}", system=FILE_ANALYSIS_SYSTEM_PROMPT)

        if ext == ".docx":
            import docx
            import io
            document = docx.Document(io.BytesIO(file_bytes))
            text = "\n".join(p.text for p in document.paragraphs)[:MAX_TEXT_CHARS]
            return self.chat(f"{prompt}\n\n---\n{text}", system=FILE_ANALYSIS_SYSTEM_PROMPT)

        if ext == ".pdf":
            b64 = base64.b64encode(file_bytes).decode("ascii")
            payload = {
                "model": self.model,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "file", "file": {
                            "filename": filename,
                            "file_data": f"data:application/pdf;base64,{b64}",
                        }},
                    ],
                }],
                "plugins": [{"id": "file-parser", "pdf": {"engine": "mistral-ocr"}}],
            }
            response = requests.post(CHAT_URL, headers=self._headers(), json=payload, timeout=60)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]

        raise NotImplementedError(f"Unsupported file type: {ext or 'unknown'}")

    def submit_video(self, prompt: str, model: str | None = None) -> dict:
        """Returns immediately with {id, polling_url, status: 'pending'} -
        the video itself takes 30s to several minutes, per OpenRouter's
        docs. Never block waiting for it here."""
        payload = {"model": model or DEFAULT_VIDEO_MODEL, "prompt": prompt}
        response = requests.post(VIDEO_URL, headers=self._headers(), json=payload, timeout=30)
        response.raise_for_status()
        return response.json()

    def poll_video(self, polling_url: str) -> dict:
        response = requests.get(polling_url, headers=self._headers(), timeout=30)
        response.raise_for_status()
        return response.json()

    def download_video(self, url: str) -> bytes:
        """unsigned_urls entries point back at OpenRouter's API and need
        the bearer token - they are not public despite not being signed."""
        response = requests.get(url, headers=self._headers(), timeout=120)
        response.raise_for_status()
        return response.content
