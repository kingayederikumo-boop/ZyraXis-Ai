from app.providers.openrouter import OpenRouterClient
from app.config import Config

# One client per feature, each with its own (optionally distinct) API key.
chat_client = OpenRouterClient(api_key=Config.OPENROUTER_API_KEY_CHAT, use_fallback=True)
roleplay_client = OpenRouterClient(api_key=Config.OPENROUTER_API_KEY_ROLEPLAY, use_fallback=True)
code_client = OpenRouterClient(api_key=Config.OPENROUTER_API_KEY_CODE, use_fallback=True)
search_client = OpenRouterClient(api_key=Config.OPENROUTER_API_KEY_SEARCH)
image_client = OpenRouterClient(api_key=Config.OPENROUTER_API_KEY_IMAGE)
file_client = OpenRouterClient(api_key=Config.OPENROUTER_API_KEY_FILE)
video_client = OpenRouterClient(api_key=Config.OPENROUTER_API_KEY_VIDEO)

ROLEPLAY_SYSTEM_PROMPT = (
    "You are ZyraXis in roleplay mode: stay in character, be creative and "
    "engaging, keep responses conversational rather than encyclopedic."
)

CODE_SYSTEM_PROMPT = (
    "You are ZyraXis's Coding Assistant. Give precise, working code. "
    "Explain tradeoffs briefly. Flag bugs or edge cases you notice even "
    "if not asked. Prefer showing corrected code over describing it."
)


class ExecutionEngine:
    """Single execution layer for all AI features."""

    def run(self, feature: str, task: str, context: dict | None = None):
        if feature == "chat":
            return chat_client.chat(task)

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
