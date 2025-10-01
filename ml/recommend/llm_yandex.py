from __future__ import annotations
from typing import Dict, Any, Optional
import os
import json
import time
import requests

# Эндпоинт REST API YandexGPT
YANDEX_LLM_URL = os.getenv(
    "YC_LLM_URL",
    "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
)

class YandexLLMError(RuntimeError):
    ...

class YandexLLM:
    """
    Мини-клиент для YandexGPT (AI Studio, REST /completion).

    Аутентификация (любой из вариантов):
      - ENV YC_API_KEY     -> заголовок "Authorization: Api-Key ..."
      - ENV YC_IAM_TOKEN   -> заголовок "Authorization: Bearer ..."
    Обязательные ENV:
      - YC_FOLDER_ID
      - (YC_API_KEY или YC_IAM_TOKEN)

    Дополнительно:
      - ENV YC_MODEL_URI (опц.)   -> gpt://<FOLDER_ID>/<model>/latest
    """

    def __init__(
        self,
        model_uri: Optional[str] = None,     # gpt://<FOLDER_ID>/yandexgpt/latest
        temperature: float = 0.2,
        max_tokens: int = 1200,
        timeout: float = 60.0,
        use_schema: bool = True,
        retries: int = 3,                    # ретраи на 429/5xx
        backoff_sec: float = 1.0,
    ):
        folder_id = os.getenv("YC_FOLDER_ID", "").strip()
        self.iam = os.getenv("YC_IAM_TOKEN", "").strip()
        self.api_key = os.getenv("YC_API_KEY", "").strip()
        if not folder_id:
            raise YandexLLMError("ENV YC_FOLDER_ID is required")
        if not (self.iam or self.api_key):
            raise YandexLLMError("Provide YC_IAM_TOKEN or YC_API_KEY")

        # Позволяем переопределять модель через ENV
        env_model_uri = os.getenv("YC_MODEL_URI", "").strip()
        self.model_uri = (
            model_uri
            or env_model_uri
            or f"gpt://{folder_id}/yandexgpt/latest"
        )

        self.temperature = float(temperature)
        # API ожидает строку для maxTokens
        self.max_tokens = str(int(max_tokens))
        self.timeout = float(timeout)
        self.use_schema = bool(use_schema)
        self.retries = int(retries)
        self.backoff_sec = float(backoff_sec)

    # -------------------- internal helpers --------------------

    def _headers(self) -> Dict[str, str]:
        if self.api_key:
            return {
                "Content-Type": "application/json",
                "Authorization": f"Api-Key {self.api_key}",
            }
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.iam}",
        }

    def _request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        last_err_txt = ""
        for attempt in range(1, self.retries + 1):
            try:
                r = requests.post(
                    YANDEX_LLM_URL,
                    headers=self._headers(),
                    json=payload,
                    timeout=self.timeout,
                )
                # Ретраим 429/5xx
                if r.status_code in (429, 500, 502, 503, 504):
                    last_err_txt = f"HTTP {r.status_code}: {r.text[:400]}"
                    time.sleep(self.backoff_sec * attempt)
                    continue
                if r.status_code != 200:
                    raise YandexLLMError(f"HTTP {r.status_code}: {r.text[:400]}")
                return r.json()
            except requests.RequestException as e:
                last_err_txt = str(e)
                time.sleep(self.backoff_sec * attempt)

        raise YandexLLMError(f"Yandex LLM request failed after retries: {last_err_txt}")

    # -------------------- public API --------------------

    def generate_json(
        self,
        system: str,
        user: str,
        json_schema: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Возвращает dict (JSON от модели), иначе бросает YandexLLMError.
        """
        if not isinstance(system, str) or not isinstance(user, str):
            raise YandexLLMError("system and user must be strings")

        body = {
            "modelUri": self.model_uri,
            "completionOptions": {
                "stream": False,
                "temperature": self.temperature,
                "maxTokens": self.max_tokens,
                # отключаем reasoning, чтобы не тратить лимиты впустую
                "reasoningOptions": {"mode": "DISABLED"},
            },
            "messages": [
                {"role": "system", "text": system},
                {"role": "user",   "text": user},
            ],
        }

        # просим строго JSON: либо jsonSchema (жёстко), либо jsonObject=true (мягко)
        if self.use_schema and json_schema:
            body["jsonSchema"] = {"schema": json_schema}
        else:
            body["jsonObject"] = True

        data = self._request(body)

        # ожидаем формат: result.alternatives[0].message.text -> JSON-строка
        try:
            text = data["result"]["alternatives"][0]["message"]["text"]
        except Exception as e:
            raise YandexLLMError(f"Bad response shape: {e}; raw={str(data)[:400]}")

        try:
            return json.loads(text)
        except Exception:
            # на всякий случай логируем первые символы, но не шумим слишком сильно
            raise YandexLLMError(f"Model didn't return valid JSON: {text[:200]}")

# -------------------- удобная обёртка (совместимость) --------------------

def yandex_llm_json(
    system: str,
    user: str,
    json_schema: Optional[Dict[str, Any]] = None,
    *,
    temperature: float = 0.2,
    max_tokens: int = 1200,
    use_schema: bool = True,
) -> Dict[str, Any]:
    """
    Удобная функция-обёртка: создаёт клиент и делает один вызов.
    Сохранена для совместимости с остальным кодом.
    """
    client = YandexLLM(
        temperature=temperature,
        max_tokens=max_tokens,
        use_schema=use_schema,
    )
    return client.generate_json(system=system, user=user, json_schema=json_schema)
