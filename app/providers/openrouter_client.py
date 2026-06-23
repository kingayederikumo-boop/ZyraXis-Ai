import requests
from app.config import Config

class OpenRouterClient:

    def chat(self, message: str):
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {Config.OPENROUTER_API_KEY}"
            },
            json={
                "model": "openai/gpt-4o-mini",
                "messages": [
                    {"role": "user", "content": message}
                ]
            }
        )

        data = response.json()
        return data["choices"][0]["message"]["content"]
