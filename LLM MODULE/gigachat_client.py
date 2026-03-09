import os
import uuid
import requests
import urllib3
from dotenv import load_dotenv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
load_dotenv()


class GigaChatClient:
    def __init__(self):
        self.auth_key = os.getenv("GIGACHAT_AUTH_KEY")
        self.scope = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
        self.model = os.getenv("GIGACHAT_MODEL", "GigaChat-2-Pro")
        self.auth_url = os.getenv(
            "GIGACHAT_AUTH_URL",
            "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
        )
        self.api_url = os.getenv(
            "GIGACHAT_API_URL",
            "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
        )

        if not self.auth_key:
            raise ValueError("Не найден GIGACHAT_AUTH_KEY в .env")

    def get_access_token(self) -> str:
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "RqUID": str(uuid.uuid4()),
            "Authorization": f"Basic {self.auth_key}",
        }

        response = requests.post(
            self.auth_url,
            headers=headers,
            data={"scope": self.scope},
            verify=False,
            timeout=30
        )
        response.raise_for_status()
        return response.json()["access_token"]

    def ask(self, system_prompt: str, user_prompt: str, temperature: float = 0.1, max_tokens: int = 1000):
        token = self.get_access_token()

        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt.strip()},
                {"role": "user", "content": user_prompt.strip()},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        response = requests.post(
            self.api_url,
            headers=headers,
            json=payload,
            verify=False,
            timeout=120
        )
        response.raise_for_status()

        data = response.json()
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})

        return {
            "content": content,
            "usage": usage,
            "raw": data
        }