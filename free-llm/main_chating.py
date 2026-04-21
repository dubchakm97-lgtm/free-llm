import re
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import html
from openai import OpenAI
import requests


class Prompt(BaseModel):
    text: str


app = FastAPI()

config_model = "qwen_coder"
config_provider = "cloud.ru"
base_url = "https://foundation-models.api.cloud.ru/v1"
api_key = os.getenv("tyga")
tg_bot_token = os.getenv("YE")
if not api_key:
    raise RuntimeError("API key not found")
if not tg_bot_token:
    raise RuntimeError("YE_TOKEN_TELEGRAM not found")

client = OpenAI(base_url=base_url, api_key=api_key)

Telegram_API = f"https://api.telegram.org/bot{tg_bot_token}"


@app.get("/")
def home():
    return FileResponse("k878j6wlqdca1.jpg")


def get_llm_answer(text: str) -> str:
    clean_text = text.encode('utf-8', 'ignore').decode('utf-8')
    completion = client.chat.completions.create(
        model="Qwen/Qwen3-Coder-Next",
        messages=[{"role": "user", "content": clean_text}]
    )
    answer = (completion.choices[0].message.content or "").encode('utf-8', 'ignore').decode("utf-8")
    return answer


@app.post('/ask')
def ask_model(prompt: Prompt):
    try:
        answer = get_llm_answer(prompt.text)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model request failed: {str(e)}")


def send_telegram_message(chat_id: int, message: str):
    response = requests.post(
        f"{Telegram_API}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": message[:4000],
            "parse_mode": "HTML"
        },
        timeout=10
    )
    print("sendMessage status:", response.status_code)
    print("sendMessage body:", response.text)


def format_for_telegram(answer: str) -> str:
    pattern = r"```(?:[a-zA-Z0-9_+-]*)?\n(.*?)```"
    parts = []
    last_end = 0

    for match in re.finditer(pattern, answer, flags=re.DOTALL):
        start, end = match.span()

        # обычный текст до блока кода
        plain_text = answer[last_end:start]
        if plain_text:
            parts.append(html.escape(plain_text))

        # содержимое блока кода
        code_text = match.group(1).rstrip("\n")
        parts.append(f"<pre><code>{html.escape(code_text)}</code></pre>")

        last_end = end

    # хвост после последнего блока кода
    tail = answer[last_end:]
    if tail:
        parts.append(html.escape(tail))

    body = "".join(parts)
    body = body.replace("###", "").replace("**", "")
    return f"<b>Ответ:</b>\n\n{body}"


@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()

    message = data.get("message")
    if not message:
        return {"ok": True}

    chat_id = message["chat"]["id"]
    text = message.get("text", "").strip()

    if text == "/start":
        send_telegram_message(chat_id, "<b>Привет!</b>\nНапиши что-нибудь.")
        return {"ok": True}

    if not text:
        send_telegram_message(chat_id, "Я понимаю только текст.")
        return {"ok": True}

    try:
        answer = get_llm_answer(text)

        formatted = format_for_telegram(answer)

        send_telegram_message(chat_id, formatted)

    except Exception as e:
        print("ERROR:", str(e))
        send_telegram_message(chat_id, "Ошибка при обработке запроса")

    return {"ok": True}
