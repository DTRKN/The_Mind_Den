"""
embeddings.py
─────────────
Генерация эмбеддингов через OpenAI text-embedding-3-small.
Возвращает numpy-независимый список float32 для хранения в SQLite BLOB.

Использование:
    from agent.embeddings import get_embedding
    vec = await get_embedding("some text")   # list[float] (1536 dims, float32)
"""

import array
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openai import AsyncOpenAI
from config import OPENAI_API_KEY, OPENROUTER_API_KEY, OPENROUTER_BASE_URL

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMS = 1536


def _get_client() -> AsyncOpenAI:
    """
    Возвращает AsyncOpenAI клиент.
    Приоритет: OPENAI_API_KEY → OPENROUTER_API_KEY (через OpenRouter /embeddings).
    """
    if OPENAI_API_KEY:
        return AsyncOpenAI(api_key=OPENAI_API_KEY)
    if OPENROUTER_API_KEY:
        return AsyncOpenAI(
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL,
        )
    raise RuntimeError(
        "Нет API-ключа для embeddings. "
        "Установите OPENAI_API_KEY или OPENROUTER_API_KEY в .env"
    )


async def get_embedding(text: str) -> list[float]:
    """
    Возвращает эмбеддинг строки как list[float] (float32, 1536 dims).

    Args:
        text: Входная строка для векторизации.

    Returns:
        Список из 1536 значений float32.
    """
    text = text.strip().replace("\n", " ")
    if not text:
        raise ValueError("Пустая строка — нельзя генерировать эмбеддинг")

    client = _get_client()
    response = await client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text,
        encoding_format="float",
    )
    raw: list[float] = response.data[0].embedding

    # Конвертируем в float32 (compact, подходит для cosine similarity)
    f32 = array.array("f", raw)
    return list(f32)


def embedding_to_blob(vec: list[float]) -> bytes:
    """Конвертирует list[float] → bytes (float32 array) для хранения в SQLite BLOB."""
    return array.array("f", vec).tobytes()


def blob_to_embedding(data: bytes) -> list[float]:
    """Конвертирует bytes из SQLite BLOB → list[float]."""
    f32 = array.array("f")
    f32.frombytes(data)
    return list(f32)


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Вычисляет косинусное сходство двух векторов (без numpy)."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
