"""
ai_handler.py
─────────────
Обёртка над OpenRouter API. Поддерживает:
  • обычный чат с историей диалога
  • переключение модели на лету
  • code assistant: tool calling для работы с файлами проекта
"""

import sys
import os
from datetime import datetime

# Добавляем корень Backend в путь для относительных импортов при запуске напрямую
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from openai import AsyncOpenAI
from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_MODEL
from db.database import get_history, save_message

# Текущая модель (меняется командой /model)
_current_model: str = OPENROUTER_MODEL

# Список популярных моделей OpenRouter
POPULAR_MODELS: list[tuple[str, str]] = [
    ("openai/gpt-4o", "GPT-4o — быстрый и умный"),
    ("openai/gpt-4o-mini", "GPT-4o Mini — экономичный"),
    ("openai/gpt-oss-120b", "GPT OSS 120B — мощная open-source модель"),
    ("anthropic/claude-3.5-sonnet", "Claude 3.5 Sonnet — отличный для текста"),
    ("anthropic/claude-3-haiku", "Claude 3 Haiku — быстрый и дешёвый"),
    ("google/gemini-flash-1.5", "Gemini Flash — быстрый мультимодальный"),
    ("meta-llama/llama-3.1-70b-instruct", "Llama 3.1 70B — open-source"),
]


def _build_system_chat() -> str:
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    return (
        f"Ты — личный AI-ассистент. Отвечай чётко, кратко и по делу. "
        f"Если пользователь пишет на русском — отвечай на русском.\n"
        f"Текущая дата и время: {now} (Europe/Moscow)."
    )


def _build_system_code() -> str:
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    return (
        f"Ты — AI-ассистент для работы с кодом. У тебя есть доступ к файловой системе проекта. "
        f"Используй инструменты (tools) для создания, редактирования и чтения файлов. "
        f"После каждого действия кратко объясняй что сделал. Пиши на русском.\n"
        f"Текущая дата и время: {now} (Europe/Moscow)."
    )


def get_client() -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url=OPENROUTER_BASE_URL,
    )


def get_model() -> str:
    return _current_model


def set_model(model_name: str) -> None:
    global _current_model
    _current_model = model_name

async def chat(user_id: int, user_message: str) -> str:
    """Обычный чат с историей диалога."""
    history = await get_history(user_id, limit=12)
    messages = [{"role": "system", "content": _build_system_chat()}] + history
    messages.append({"role": "user", "content": user_message})

    client = get_client()
    response = await client.chat.completions.create(
        model=_current_model,
        messages=messages,
        max_tokens=2048,
    )
    reply = response.choices[0].message.content or ""

    # Сохраняем в историю
    await save_message(user_id, "user", user_message)
    await save_message(user_id, "assistant", reply)

    return reply
