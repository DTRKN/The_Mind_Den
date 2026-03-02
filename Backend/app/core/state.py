"""
core/state.py
─────────────
Глобальное состояние приложения.
Используется роутерами API для доступа к запущенному Telegram-боту и uptime.
"""

import time
from typing import Optional

from telegram.ext import Application


class AppState:
    tg_app: Optional[Application] = None
    start_time: float = 0.0

    @classmethod
    def set_started(cls, app: Application) -> None:
        cls.tg_app = app
        cls.start_time = time.time()

    @classmethod
    def uptime_seconds(cls) -> int:
        if cls.start_time == 0.0:
            return 0
        return int(time.time() - cls.start_time)

    @classmethod
    def bot_running(cls) -> bool:
        return cls.tg_app is not None and cls.tg_app.running
