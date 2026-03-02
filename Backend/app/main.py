"""
app/main.py
───────────
Единственная точка входа. Один процесс, один event loop.

Запуск:
    cd Backend
    python app/main.py
"""

import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn
from telegram.ext import ApplicationBuilder

from core.logging import setup_logging, get_logger
from core.state import AppState
from config import TELEGRAM_BOT_TOKEN, ALLOWED_USER_IDS
from db.database import create_tables
from bot.handlers import register_handlers
from scheduler.scheduler import get_scheduler, load_pending_reminders
from skills.loader import reload_skills
from api.app import create_app

setup_logging()
logger = get_logger(__name__)


async def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не задан в .env!")
        sys.exit(1)

    if not ALLOWED_USER_IDS:
        logger.warning("ALLOWED_USER_IDS пуст — бот доступен ВСЕМ пользователям!")

    # ── БД ───────────────────────────────────────────────────────────────────
    await create_tables()
    logger.info("БД инициализирована")

    # ── Планировщик ──────────────────────────────────────────────────────────
    scheduler = get_scheduler()
    scheduler.start()
    logger.info("Scheduler запущен")

    # ── Telegram-бот ─────────────────────────────────────────────────────────
    tg_app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    register_handlers(tg_app)

    async with tg_app:

        await tg_app.start()
        await tg_app.updater.start_polling(
            drop_pending_updates=True,
            allowed_updates=["message", "callback_query"],
        )

        await load_pending_reminders(tg_app)
        reload_skills()
        AppState.set_started(tg_app)

        logger.info("Whitelist: %s", ALLOWED_USER_IDS)
        logger.info("Бот запущен. API: http://localhost:8000")

        # ── FastAPI в том же event loop ───────────────────────────────────────
        api = create_app()
        config = uvicorn.Config(
            api,
            host="0.0.0.0",
            port=8000,
            log_level="warning",
            workers=1,
        )
        server = uvicorn.Server(config)
        await server.serve()  # блокирует до Ctrl+C

        # ── Остановка ─────────────────────────────────────────────────────────
        logger.info("Завершение работы...")
        await tg_app.updater.stop()
        await tg_app.stop()

    scheduler.shutdown(wait=False)
    logger.info("Готово.")


if __name__ == "__main__":
    asyncio.run(main())

