"""
api/messages.py
───────────────
История сообщений пользователей.
"""

from fastapi import APIRouter

from db.database import get_all_messages, get_stats
from core.state import AppState

router = APIRouter(prefix="/api", tags=["messages"])


@router.get("/stats")
async def stats():
    """Базовая статистика для Dashboard."""
    data = await get_stats()
    data["uptime_seconds"] = AppState.uptime_seconds()
    return data


@router.get("/messages")
async def messages(limit: int = 100, offset: int = 0):
    """История сообщений (все пользователи, последние сначала)."""
    return await get_all_messages(limit=limit, offset=offset)
