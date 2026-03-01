"""
memory_tool.py
──────────────
Инструмент долгосрочной памяти агента на базе Pinecone (векторная БД).

Операции:
  save   — генерирует embedding и сохраняет в Pinecone (upsert)
  search — семантический поиск воспоминаний по запросу
  list   — возвращает последние N воспоминаний пользователя

Архитектура:
  Векторное хранилище  → Pinecone serverless index (cosine, 1536 dims)
  Метаданные           → хранятся прямо в Pinecone metadata
  ID вектора           → "mem_{user_id}_{uuid4}"

Использование:
    from agent.tools.memory_tool import MemoryToolInput, run_memory_tool
    result = await run_memory_tool(MemoryToolInput(action="save", content="..."), user_id)
"""

import logging
import sys
import os
import uuid
from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, Field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import PINECONE_API_KEY, PINECONE_INDEX_NAME, VECTOR_SEARCH_LIMIT
from agent.embeddings import get_embedding

logger = logging.getLogger(__name__)

# ─── Константы Pinecone ────────────────────────────────────────────────────────

EMBEDDING_DIMS = 1536
EMBEDDING_METRIC = "cosine"
PINECONE_CLOUD = "aws"
PINECONE_REGION = "us-east-1"

# ─── Pydantic модель ───────────────────────────────────────────────────────────


class MemoryToolInput(BaseModel):
    """Входные параметры для memory_tool."""

    action: Literal["save", "search", "list"] = Field(
        description="save — сохранить, search — найти, list — список"
    )
    content: Optional[str] = Field(
        default=None,
        description="Текст для сохранения (action=save) или поисковый запрос (action=search)",
    )
    limit: Optional[int] = Field(
        default=None,
        description="Максимальное число результатов (action=search, action=list)",
    )


# ─── Pinecone клиент (lazy singleton) ─────────────────────────────────────────

_pinecone_index = None


def _get_index():
    """
    Возвращает Pinecone Index (lazy init).
    Создаёт serverless индекс, если его ещё нет.
    """
    global _pinecone_index
    if _pinecone_index is not None:
        return _pinecone_index

    if not PINECONE_API_KEY:
        raise RuntimeError(
            "PINECONE_API_KEY не задан. Добавьте его в .env"
        )

    from pinecone import Pinecone, ServerlessSpec

    pc = Pinecone(api_key=PINECONE_API_KEY)

    # Создаём индекс, если не существует
    if not pc.has_index(PINECONE_INDEX_NAME):
        logger.info(f"Создаю Pinecone индекс '{PINECONE_INDEX_NAME}'...")
        pc.create_index(
            name=PINECONE_INDEX_NAME,
            dimension=EMBEDDING_DIMS,
            metric=EMBEDDING_METRIC,
            spec=ServerlessSpec(cloud=PINECONE_CLOUD, region=PINECONE_REGION),
        )
        logger.info(f"Pinecone индекс '{PINECONE_INDEX_NAME}' создан")

    _pinecone_index = pc.Index(PINECONE_INDEX_NAME)
    logger.info(f"Pinecone индекс '{PINECONE_INDEX_NAME}' подключён")
    return _pinecone_index


# ─── Операции ─────────────────────────────────────────────────────────────────


async def _save_memory(user_id: int, content: str) -> dict:
    """Генерирует embedding и сохраняет воспоминание в Pinecone."""
    embedding = await get_embedding(content)
    vector_id = f"mem_{user_id}_{uuid.uuid4().hex}"
    created_at = datetime.now(timezone.utc).isoformat()

    index = _get_index()
    index.upsert(
        vectors=[
            {
                "id": vector_id,
                "values": embedding,
                "metadata": {
                    "user_id": user_id,
                    "content": content,
                    "created_at": created_at,
                },
            }
        ],
        namespace=f"user_{user_id}",
    )

    logger.info(f"Memory saved: id={vector_id}, user={user_id}")
    return {"success": True, "id": vector_id, "content": content}


async def _search_memory(user_id: int, query: str, limit: int) -> dict:
    """Семантический поиск воспоминаний по косинусному сходству."""
    embedding = await get_embedding(query)

    index = _get_index()
    result = index.query(
        vector=embedding,
        top_k=limit,
        include_metadata=True,
        namespace=f"user_{user_id}",
    )

    memories = []
    for match in result.matches:
        meta = match.metadata or {}
        memories.append(
            {
                "id": match.id,
                "content": meta.get("content", ""),
                "score": round(match.score, 4),
                "created_at": meta.get("created_at", ""),
            }
        )

    return {"success": True, "memories": memories, "count": len(memories)}


async def _list_memory(user_id: int, limit: int) -> dict:
    """
    Список последних воспоминаний пользователя.
    Pinecone не поддерживает ORDER BY, поэтому выполняем query
    с нулевым вектором и large top_k, фильтруя по user_id через namespace.
    """
    index = _get_index()
    # Запрос с нулевым вектором — возвращает "случайные" результаты
    zero_vec = [0.0] * EMBEDDING_DIMS
    result = index.query(
        vector=zero_vec,
        top_k=min(limit, 100),
        include_metadata=True,
        namespace=f"user_{user_id}",
    )

    memories = []
    for match in result.matches:
        meta = match.metadata or {}
        memories.append(
            {
                "id": match.id,
                "content": meta.get("content", ""),
                "created_at": meta.get("created_at", ""),
            }
        )

    return {"success": True, "memories": memories, "count": len(memories)}


# ─── Основная точка входа ──────────────────────────────────────────────────────


async def run_memory_tool(data: MemoryToolInput, user_id: int) -> dict:
    """Диспетчер: делегирует вызов нужной операции на основе action."""
    limit = data.limit or VECTOR_SEARCH_LIMIT

    if data.action == "save":
        if not data.content:
            return {"success": False, "error": "Поле 'content' обязательно для action=save"}
        return await _save_memory(user_id, data.content)

    if data.action == "search":
        if not data.content:
            return {"success": False, "error": "Поле 'content' обязательно для action=search"}
        return await _search_memory(user_id, data.content, limit)

    if data.action == "list":
        return await _list_memory(user_id, limit)

    return {"success": False, "error": f"Неизвестный action: {data.action}"}


# ─── Вспомогательная: получить контекст для системного промпта ────────────────


async def get_memory_context(user_id: int, query: str) -> str:
    """
    Автоматически ищет релевантные воспоминания и возвращает
    готовый текст для вставки в system prompt.

    Возвращает пустую строку, если воспоминаний нет или Pinecone недоступен.
    """
    if not PINECONE_API_KEY:
        return ""

    try:
        result = await _search_memory(user_id, query, limit=VECTOR_SEARCH_LIMIT)
        memories = result.get("memories", [])
        if not memories:
            return ""

        lines = ["[Из долгосрочной памяти]"]
        for m in memories:
            if m.get("content"):
                lines.append(f"- {m['content']}")
        return "\n".join(lines)
    except Exception as e:
        logger.warning(f"get_memory_context error (non-fatal): {e}")
        return ""
