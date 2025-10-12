# ml/ping_gpt.py
import os, json, requests
from dotenv import load_dotenv
load_dotenv()

FOLDER = os.getenv("YC_FOLDER_ID")
API    = os.getenv("YC_API_KEY")
URL    = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

assert FOLDER, "YC_FOLDER_ID пуст"
assert API, "YC_API_KEY пуст"

headers = {"Authorization": f"Api-Key {API}", "Content-Type": "application/json"}
body = {
    "modelUri": f"gpt://{FOLDER}/yandexgpt/latest",
    "completionOptions": {"stream": False, "temperature": 0.2, "maxTokens": "200"},
    # без строгой схемы — просто попросим JSON
    "jsonObject": True,
    "messages": [
        {"role": "system", "text": "Return ONLY JSON."},
        {"role": "user",   "text": "Верни JSON {\"ok\": true}"},
    ],
}

try:
    r = requests.post(URL, headers=headers, json=body, timeout=60)
    print("HTTP:", r.status_code)
    print("TEXT:", r.text[:400])
    r.raise_for_status()
    data = r.json()
    text = data["result"]["alternatives"][0]["message"]["text"]
    print("PARSED JSON:", json.loads(text))
except Exception as e:
    print("ERROR:", e)
