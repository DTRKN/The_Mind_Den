"""
main.py
───────
Точка входа FastAPI: управляет lifespan telegram-бота и APScheduler.
Запуск: uvicorn app.main:app --host 0.0.0.0 --port 8000
"""

import sys
import os
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime

# Добавляем app/ в Python path, чтобы `from bot.handlers` находил app/bot/handlers.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from telegram.ext import ApplicationBuilder

from config import TELEGRAM_BOT_TOKEN, ALLOWED_USER_IDS
from db.database import (
    create_tables, get_stats, get_all_messages,
    get_all_active_reminders_api, delete_reminder_api, add_reminder_api,
)
from bot.handlers import register_handlers
from scheduler.scheduler import get_scheduler, load_pending_reminders
from skills.loader import reload_skills, get_loaded_skills

# ─── Логирование ──────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# ─── Глобальные переменные ────────────────────────────────────────────────────
_tg_app = None
_start_time: float = 0.0


def get_tg_app():
    return _tg_app


# ─── FastAPI lifespan ──────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    global _tg_app, _start_time
    _start_time = time.time()

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

    # ── Загрузка скиллов ─────────────────────────────────────────────────
    reload_skills()

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
    """Расширенная проверка: статус бота, шедулера, uptime."""
    scheduler = get_scheduler()
    return {
        "status": "ok",
        "bot_running": _tg_app is not None and _tg_app.running,
        "scheduler_running": scheduler.running,
        "version": "0.1.0",
    }


@app.get("/api/stats")
async def api_stats():
    """Базовая статистика для Dashboard."""
    stats = await get_stats()
    stats["uptime_seconds"] = int(time.time() - _start_time) if _start_time else 0
    return stats


@app.get("/api/messages")
async def api_messages(limit: int = 100, offset: int = 0):
    """История сообщений (все пользователи, последние сначала)."""
    return await get_all_messages(limit=limit, offset=offset)


# ─── Reminders CRUD ────────────────────────────────────────────────────────────

class ReminderCreateRequest(BaseModel):
    user_id: int = 0
    message: str
    next_run: str  # ISO datetime string
    is_recurring: bool = False
    cron_expr: str | None = None


@app.get("/api/reminders")
async def api_reminders_list():
    """Список всех напоминаний."""
    return await get_all_active_reminders_api()


@app.post("/api/reminders", status_code=201)
async def api_reminders_create(body: ReminderCreateRequest):
    """Создать напоминание через REST API."""
    try:
        remind_at = datetime.fromisoformat(body.next_run)
    except ValueError:
        raise HTTPException(status_code=422, detail="next_run: неверный формат ISO datetime")
    record = await add_reminder_api(
        user_id=body.user_id,
        text=body.message,
        remind_at=remind_at,
        cron_expr=body.cron_expr,
        is_recurring=body.is_recurring,
    )
    return record


@app.delete("/api/reminders/{reminder_id}", status_code=204)
async def api_reminders_delete(reminder_id: int):
    """Удалить напоминание по ID."""
    deleted = await delete_reminder_api(reminder_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Напоминание не найдено")


# ─── Skills CRUD ───────────────────────────────────────────────────────────────

class SkillCreateRequest(BaseModel):
    name: str
    title: str
    description: str
    content: str = ""


@app.get("/api/skills")
async def api_skills_list():
    """Список загруженных скиллов."""
    return get_loaded_skills()


@app.post("/api/skills", status_code=201)
async def api_skills_create(body: SkillCreateRequest):
    """Создать новый скилл (папка + SKILL.md) и перезагрузить кеш."""
    from agent.tools.skill_tool import SkillToolInput, run_skill_tool
    try:
        data = SkillToolInput(
            name=body.name,
            title=body.title,
            description=body.description,
            content=body.content,
        )
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))
    result = await run_skill_tool(data)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Ошибка создания скилла"))
    # Вернуть созданный скилл из кеша
    skills = get_loaded_skills()
    created = next((s for s in skills if s["name"] == data.name), result)
    return created


# ─── Локальный запуск ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)

