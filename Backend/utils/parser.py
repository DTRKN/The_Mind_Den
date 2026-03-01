import re
from datetime import datetime
from typing import Optional, Tuple
import dateparser

# Ключевые слова, которые указывают на намерение создать напоминание
REMINDER_TRIGGERS = (
    "напомни", "напомнить", "напоминай", "remind", "reminder",
    "поставь напоминание", "создай напоминание",
)


def _get_dateparser_settings() -> dict:
    return {
        "PREFER_DATES_FROM": "future",
        "RETURN_AS_TIMEZONE_AWARE": False,
        "PREFER_DAY_OF_MONTH": "first",
        "RELATIVE_BASE": datetime.now(),
        "PARSERS": ["relative-time", "absolute-time", "timestamp"],
    }


def _normalize_text(text: str) -> str:
    """
    Нормализует время в тексте перед парсингом:
    - "15.07" → "15:07"  (точка вместо двоеточия)
    - "15.7"  → "15:07"
    - "1507"  → "15:07"  (4 цифры подряд как время)
    - Убирает точку в конце предложения (чтобы "15:07." не ломало парсер)
    """
    # "в 15.07" или просто "15.07" — точка как разделитель времени
    # Только если ЭТО похоже на время (часы 0-23, минуты 0-59)
    def replace_dot_time(m: re.Match) -> str:
        h, mn = m.group(1), m.group(2)
        if int(h) <= 23 and int(mn) <= 59:
            return f"{h}:{mn}"
        return m.group(0)  # не трогаем, если не время

    result = re.sub(r"\b([01]?\d|2[0-3])\.([0-5]\d)\b", replace_dot_time, text)

    # "1507" → "15:07" (4 цифры без разделителя, контекст "в 1507")
    def replace_compact_time(m: re.Match) -> str:
        s = m.group(1)
        h, mn = s[:2], s[2:]
        if int(h) <= 23 and int(mn) <= 59:
            return f"в {h}:{mn}"
        return m.group(0)

    result = re.sub(r"\bв\s+([01]\d[0-5]\d|2[0-3][0-5]\d)\b", replace_compact_time, result)

    # Убираем точку перед пробелом или в конце — "съесть морковь." → "съесть морковь"
    result = result.rstrip(". ")

    return result


def is_reminder_request(text: str) -> bool:
    """Проверяет, является ли сообщение запросом на создание напоминания."""
    lower = text.lower()
    return any(trigger in lower for trigger in REMINDER_TRIGGERS)


def parse_reminder(text: str) -> Tuple[Optional[datetime], str]:
    """
    Разбирает текст напоминания.
    Возвращает (datetime | None, текст_напоминания).

    Поддерживаемые форматы времени:
      "в 17:30", "в 17.30", "в 1730", "сегодня в 15:07",
      "завтра в 9:00", "через 2 часа", "через 30 минут"
    """
    # Нормализуем форматы времени
    text = _normalize_text(text)

    # Убираем триггерные слова из текста
    clean = text
    for trigger in sorted(REMINDER_TRIGGERS, key=len, reverse=True):
        clean = re.sub(re.escape(trigger), "", clean, flags=re.IGNORECASE)
    # Убираем лишние слова-паразиты
    clean = re.sub(r"\bмне\b", "", clean, flags=re.IGNORECASE)
    clean = clean.strip(" ,.:!?")

    settings = _get_dateparser_settings()

    # Пробуем распарсить очищенный текст
    dt = dateparser.parse(clean, languages=["ru", "en"], settings=settings)

    if dt:
        reminder_text = _extract_reminder_text(clean)
    else:
        # Пробуем исходный (нормализованный) текст
        dt = dateparser.parse(text, languages=["ru", "en"], settings=settings)
        reminder_text = _extract_reminder_text(clean) if dt else clean

    return dt, reminder_text.strip() or clean.strip()


def _extract_reminder_text(text: str) -> str:
    """Удаляет временные паттерны из текста, оставляя суть напоминания."""
    patterns = [
        r"\bв\s+\d{1,2}:\d{2}\b",
        r"\bв\s+\d{1,2}\s*час(а|ов)?\b",
        r"\bсегодня\b",
        r"\bзавтра\b",
        r"\bпослезавтра\b",
        r"\bчерез\s+\d+\s*(минут|час|часа|часов|мин|ч)\b",
        r"\bутром\b",
        r"\bвечером\b",
        r"\bдн[её]м\b",
        r"\bночью\b",
        r"\bмне\b",
    ]
    result = text
    for p in patterns:
        result = re.sub(p, "", result, flags=re.IGNORECASE)
    result = re.sub(r"\s{2,}", " ", result)
    result = result.strip(" ,.:!?")
    return result
    return result
