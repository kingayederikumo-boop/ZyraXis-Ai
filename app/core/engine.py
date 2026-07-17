from app.providers.openrouter import OpenRouterClient
from app.providers.gemini import GeminiClient
from app.config import Config

# One client per feature, each with its own (optionally distinct) API key.
chat_client = OpenRouterClient(api_key=Config.OPENROUTER_API_KEY_CHAT, use_fallback=True)
roleplay_client = OpenRouterClient(api_key=Config.OPENROUTER_API_KEY_ROLEPLAY, use_fallback=True)
code_client = OpenRouterClient(api_key=Config.OPENROUTER_API_KEY_CODE, use_fallback=True)
search_client = OpenRouterClient(api_key=Config.OPENROUTER_API_KEY_SEARCH)
# Switched from OpenRouter's Images API (402 Payment Required without a
# funded balance) to Gemini's free tier (Nano Banana 2).
image_client = GeminiClient(api_key=Config.GEMINI_API_KEY)
file_client = OpenRouterClient(api_key=Config.OPENROUTER_API_KEY_FILE)
video_client = OpenRouterClient(api_key=Config.OPENROUTER_API_KEY_VIDEO)

IDENTITY_INSTRUCTION = (
    "If asked who made you, who created you, or what company/AI is behind "
    "you, answer: Rex AI. Never mention OpenRouter, OpenAI, Anthropic, "
    "Google, or any other underlying model provider."
)

CHAT_SYSTEM_PROMPT = (
    "You are ZyraXis, a warm and direct AI assistant. Write in clear, "
    "natural, modern language - conversational but substantive, never "
    "stiff, archaic, or overly formal. Get to the point, use plain words, "
    "and let genuine warmth come through without being saccharine.\n\n"
    + IDENTITY_INSTRUCTION
)

ROLEPLAY_SYSTEM_PROMPT = (
    "You are ZyraXis in roleplay mode: stay in character, be creative and "
    "engaging, keep responses conversational rather than encyclopedic.\n\n"
    + IDENTITY_INSTRUCTION
)

CODE_SYSTEM_PROMPT = (
    "You are ZyraXis's Coding Assistant. Give precise, working code. "
    "Explain tradeoffs briefly. Flag bugs or edge cases you notice even "
    "if not asked. Prefer showing corrected code over describing it.\n\n"
    + IDENTITY_INSTRUCTION
)


class ExecutionEngine:
    """Single execution layer for all AI features."""

    def run(self, feature: str, task: str, context: dict | None = None):
        if feature == "chat":
            return chat_client.chat(task, system=CHAT_SYSTEM_PROMPT)

        if feature == "roleplay":
            return roleplay_client.chat(task, system=ROLEPLAY_SYSTEM_PROMPT)

        if feature == "code":
            return code_client.chat(task, system=CODE_SYSTEM_PROMPT)

        if feature == "search":
            return search_client.search(task)

        if feature == "image":
            return image_client.generate_image(task)

        if feature == "file":
            # context is required here - file_bytes/filename come from the
            # Telegram document the user uploaded, not from the text prompt.
            if not context or "file_bytes" not in context:
                raise ValueError("file feature requires context={'file_bytes':..., 'filename':...}")
            return file_client.analyze_file(context["file_bytes"], context["filename"], task)

        if feature == "video":
            # Genuinely async - returns job info immediately, not the video
            # itself. Caller (orchestrator/consumer) is responsible for
            # tracking the job and delivering the result later.
            return video_client.submit_video(task)

        return chat_client.chat(task)
