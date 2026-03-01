"""
main.py
───────
Точка входа FastAPI: управляет lifespan telegram-бота и APScheduler.
Запуск: uvicorn app.main:app --host 0.0.0.0 --port 8000
"""

import sys
import os
import logging
from contextlib import asynccontextmanager

# Добавляем app/ в Python path, чтобы `from bot.handlers` находил app/bot/handlers.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from telegram.ext import ApplicationBuilder

from config import TELEGRAM_BOT_TOKEN, ALLOWED_USER_IDS
from db.database import create_tables, get_stats, get_all_messages
from bot.handlers import register_handlers
from scheduler.scheduler import get_scheduler, load_pending_reminders

# ─── Логирование ──────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# ─── Глобальный экземпляр telegram Application ────────────────────────────────
_tg_app = None


def get_tg_app():
    return _tg_app


# ─── FastAPI lifespan ──────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    global _tg_app

    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не задан в .env!")
        sys.exit(1)

    if not ALLOWED_USER_IDS:
        logger.warning("ALLOWED_USER_IDS пуст — бот доступен ВСЕМ пользователям!")

    # ── Инициализация БД ─────────────────────────────────────────────────────
    await create_tables()
    logger.info("БД инициализирована")

    # ── Запуск APScheduler ───────────────────────────────────────────────────
    scheduler = get_scheduler()
    scheduler.start()
    logger.info("Scheduler started")

    # ── Инициализация telegram-бота ──────────────────────────────────────────
    _tg_app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    register_handlers(_tg_app)

    await _tg_app.initialize()
    await _tg_app.start()
    await _tg_app.updater.start_polling(drop_pending_updates=True)

    await load_pending_reminders(_tg_app)
    logger.info(f"Whitelist: {ALLOWED_USER_IDS}")
    logger.info("Бот запущен (polling). FastAPI слушает на :8000")

    yield  # ← FastAPI работает

    # ── Остановка ────────────────────────────────────────────────────────────
    logger.info("Завершение работы...")
    await _tg_app.updater.stop()
    await _tg_app.stop()
    await _tg_app.shutdown()
    scheduler.shutdown(wait=False)
    logger.info("Бот и планировщик остановлены")


# ─── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="The Mind Den",
    description="Backend API для Mind Den бота",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    return {"status": "ok"}


# ─── API v1 ────────────────────────────────────────────────────────────────────

@app.get("/api/health")
async def api_health():
    """Проверка доступности сервиса."""
    return {"status": "ok"}


@app.get("/api/stats")
async def api_stats():
    """Базовая статистика для Dashboard."""
    stats = await get_stats()
    return stats


@app.get("/api/messages")
async def api_messages(limit: int = 100, offset: int = 0):
    """История сообщений (все пользователи, последние сначала)."""
    messages = await get_all_messages(limit=limit, offset=offset)
    return messages


# ─── Локальный запуск ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)

