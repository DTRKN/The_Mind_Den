"""
api/health.py
─────────────
Эндпоинты проверки работоспособности сервиса.
"""

from fastapi import APIRouter

from core.state import AppState
from scheduler.scheduler import get_scheduler

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_simple():
    """Быстрая проверка — сервис жив."""
    return {"status": "ok"}


@router.get("/api/health")
async def health_detailed():
    """Расширенная проверка: статус бота, планировщика, uptime."""
    scheduler = get_scheduler()
    return {
        "status": "ok",
        "bot_running": AppState.bot_running(),
        "scheduler_running": scheduler.running,
        "uptime_seconds": AppState.uptime_seconds(),
        "version": "0.1.0",
    }
