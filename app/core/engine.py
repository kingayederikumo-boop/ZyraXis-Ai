from app.providers.openrouter import OpenRouterClient

client = OpenRouterClient()

class ExecutionEngine:
    """Single execution layer for all AI features (V1.4)."""

    def run(self, feature: str, task: str, context: dict | None = None):
        """
        Unified entry point for all AI execution paths.
        Future expansion: roleplay, tools, image, multimodal routing.
        """

        if feature == "chat":
            return client.chat(task)

        # Safe fallback prevents system breakage
        return client.chat(task)
