"""
core/logging.py
───────────────
Централизованная настройка логирования.
Вызывать setup_logging() один раз при старте приложения.
"""

import logging
import sys


def setup_logging(level: int = logging.INFO) -> None:
    """Настраивает root-логгер и выключает шум от сторонних библиотек."""
    logging.basicConfig(
        stream=sys.stdout,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
        level=level,
    )
    # Снижаем уровень шума от сетевых библиотек
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Возвращает логгер с заданным именем."""
    return logging.getLogger(name)
