"""
web_search_tool.py
──────────────────
Инструмент агента для поиска в интернете через Tavily Search API.

Pydantic модель: WebSearchToolInput
Точка входа:    run_web_search_tool(data) -> dict
"""

import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import httpx
from pydantic import BaseModel, Field
from typing import Literal

from config import TAVILY_API_KEY

logger = logging.getLogger(__name__)

TAVILY_URL = "https://api.tavily.com/search"


class WebSearchToolInput(BaseModel):
    """Параметры для веб-поиска через Tavily."""

    query: str = Field(..., description="Поисковый запрос")
    search_depth: Literal["basic", "advanced"] = Field(
        default="basic",
        description="Глубина поиска: basic (быстро) или advanced (подробно)",
    )
    max_results: int = Field(default=5, ge=1, le=10, description="Максимальное число результатов")


async def run_web_search_tool(data: WebSearchToolInput) -> dict:
    """
    Выполняет поиск через Tavily API и возвращает список результатов.

    Returns:
        {"success": True, "results": [{"title": ..., "url": ..., "content": ...}]}
        {"success": False, "error": ...}
    """
    if not TAVILY_API_KEY:
        logger.warning("TAVILY_API_KEY не задан — web_search_tool недоступен")
        return {
            "success": False,
            "error": "Поиск недоступен: TAVILY_API_KEY не настроен.",
        }

    payload = {
        "api_key": TAVILY_API_KEY,
        "query": data.query,
        "search_depth": data.search_depth,
        "max_results": data.max_results,
        "include_answer": True,
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(TAVILY_URL, json=payload)
            response.raise_for_status()
            data_json = response.json()

        results = []
        for item in data_json.get("results", []):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "content": item.get("content", "")[:500],  # ограничиваем размер
            })

        # Если есть прямой ответ Tavily — добавляем
        answer = data_json.get("answer")

        logger.info(f"WebSearch: '{data.query}' → {len(results)} результатов")
        return {
            "success": True,
            "query": data.query,
            "answer": answer,
            "results": results,
        }

    except httpx.HTTPStatusError as e:
        logger.error(f"Tavily HTTP error: {e.response.status_code} {e.response.text[:200]}")
        return {"success": False, "error": f"Ошибка Tavily API: {e.response.status_code}"}
    except Exception as e:
        logger.error(f"WebSearch error: {e}")
        return {"success": False, "error": str(e)}
