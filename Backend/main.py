"""
ВНИМАНИЕ: этот файл устарел и НЕ должен использоваться.

Единственная правильная точка входа:

    cd Backend
    uvicorn app.main:app --host 0.0.0.0 --port 8000

Или в режиме разработки:

    cd Backend
    python app/main.py
"""

raise SystemExit(
    "\n"
    "  ╔══════════════════════════════════════════════════════════╗\n"
    "  ║  УСТАРЕВШИЙ ФАЙЛ — используйте app/main.py              ║\n"
    "  ║                                                          ║\n"
    "  ║  Правильный запуск (из папки Backend/):                 ║\n"
    "  ║    uvicorn app.main:app --host 0.0.0.0 --port 8000      ║\n"
    "  ╚══════════════════════════════════════════════════════════╝\n"
)

# ─── PID-lock: защита от двойного запуска ─────────────────────────────────────
_LOCK_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "bot.pid")
_LOCK_FILE = os.path.normpath(_LOCK_FILE)

def _acquire_lock() -> None:
    """Проверяет, не запущен ли уже другой экземпляр бота. Если да — завершает процесс."""
    os.makedirs(os.path.dirname(_LOCK_FILE), exist_ok=True)
    if os.path.exists(_LOCK_FILE):
        try:
            with open(_LOCK_FILE) as f:
                old_pid = int(f.read().strip())
            import psutil
            if psutil.pid_exists(old_pid):
                print(f"[LOCK] Бот уже запущен (PID {old_pid}). Завершение.", flush=True)
                sys.exit(1)
        except (ValueError, ImportError, OSError):
            pass  # Файл повреждён или psutil недоступен — продолжаем
    with open(_LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))
    atexit.register(_release_lock)

def _release_lock() -> None:
    try:
        os.remove(_LOCK_FILE)
    except OSError:
        pass

_acquire_lock()

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

