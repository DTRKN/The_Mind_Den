"""
main.py
───────
Точка входа: инициализация БД → запуск планировщика → запуск бота.
Запуск: python main.py (из папки Backend/)
"""

import sys
import os
import logging

# Добавляем Backend/ в Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from telegram.ext import ApplicationBuilder, Application

from config import TELEGRAM_BOT_TOKEN, ALLOWED_USER_IDS
from db.database import create_tables
from bot.handlers import register_handlers
from scheduler.scheduler import start_scheduler, stop_scheduler, load_pending_reminders

# ─── Логирование ──────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


async def post_init(application: Application) -> None:
    """Вызывается один раз после старта бота."""
    await create_tables()
    logger.info("БД инициализирована")
    start_scheduler()
    await load_pending_reminders(application)
    logger.info(f"Whitelist: {ALLOWED_USER_IDS}")
    logger.info("🤖 Бот запущен. Нажми Ctrl+C для остановки.")


async def post_shutdown(application: Application) -> None:
    stop_scheduler()


def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не задан в .env!")
        sys.exit(1)

    if not ALLOWED_USER_IDS:
        logger.warning("ALLOWED_USER_IDS пуст — бот доступен ВСЕМ пользователям!")

    app = (
        ApplicationBuilder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    register_handlers(app)
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()

