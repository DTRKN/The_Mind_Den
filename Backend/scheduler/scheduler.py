"""
scheduler.py
────────────
APScheduler для отправки напоминаний в нужное время.

При старте бота загружает все pending-напоминания из БД и регистрирует jobs.
При добавлении нового напоминания — динамически добавляет job.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from telegram.ext import Application

from db.database import get_pending_reminders, mark_reminder_sent

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


def get_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler(
            jobstores={"default": MemoryJobStore()},
            timezone="Europe/Moscow",
        )
    return _scheduler


async def _send_reminder(app: Application, reminder_id: int, user_id: int, text: str) -> None:
    """Job: отправляет напоминание пользователю."""
    try:
        await app.bot.send_message(
            chat_id=user_id,
            text=f"⏰ *Напоминание #{reminder_id}*\n\n{text}",
            parse_mode="Markdown",
        )
        await mark_reminder_sent(reminder_id)
        logger.info(f"Напоминание #{reminder_id} отправлено пользователю {user_id}")
    except Exception as e:
        logger.error(f"Ошибка отправки напоминания #{reminder_id}: {e}")


async def schedule_reminder(
    app: Application,
    reminder_id: int,
    user_id: int,
    text: str,
    remind_at: datetime,
) -> None:
    """Добавляет одиночный job для отправки напоминания."""
    scheduler = get_scheduler()
    scheduler.add_job(
        _send_reminder,
        trigger="date",
        run_date=remind_at,
        args=[app, reminder_id, user_id, text],
        id=f"reminder_{reminder_id}",
        replace_existing=True,
        misfire_grace_time=300,  # Если пропустили — всё равно отправить (до 5 мин)
    )
    logger.info(f"Запланировано напоминание #{reminder_id} на {remind_at}")


async def load_pending_reminders(app: Application) -> None:
    """При старте загружает все невыполненные напоминания из БД."""
    now = datetime.now()
    reminders = await get_pending_reminders()
    loaded = 0

    for r in reminders:
        remind_at = datetime.fromisoformat(r["remind_at"])

        if remind_at <= now:
            # Просроченные — отправляем сразу
            await _send_reminder(app, r["id"], r["user_id"], r["text"])
        else:
            await schedule_reminder(app, r["id"], r["user_id"], r["text"], remind_at)
            loaded += 1

    logger.info(f"Загружено {loaded} напоминаний из БД")


def start_scheduler() -> None:
    scheduler = get_scheduler()
    if not scheduler.running:
        scheduler.start()
        logger.info("Планировщик запущен")


def stop_scheduler() -> None:
    scheduler = get_scheduler()
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Планировщик остановлен")
