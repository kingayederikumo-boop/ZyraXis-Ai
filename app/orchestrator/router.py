from app.providers.openrouter_client import OpenRouterClient

client = OpenRouterClient()

class Orchestrator:

    def handle_message(self, text: str):
        return client.chat(text)
