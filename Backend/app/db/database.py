import sqlite3
import aiosqlite
import sqlite_vec
from datetime import datetime
from config import DB_PATH


async def _load_vec_extension(db: aiosqlite.Connection) -> None:
    """Загружает sqlite-vec внутри потока aiosqlite (thread-safe)."""
    def _inner():
        db._connection.enable_load_extension(True)  # type: ignore[attr-defined]
        sqlite_vec.load(db._connection)  # type: ignore[attr-defined]
        db._connection.enable_load_extension(False)  # type: ignore[attr-defined]
    await db._execute(_inner)  # type: ignore[attr-defined]


async def create_tables() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        # Загружаем sqlite-vec через aiosqlite-thread (thread-safe)
        await _load_vec_extension(db)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id      INTEGER NOT NULL,
                text         TEXT    NOT NULL,
                remind_at    TEXT    NOT NULL,
                cron_expr    TEXT,
                is_recurring INTEGER NOT NULL DEFAULT 0,
                created_at   TEXT    NOT NULL DEFAULT (datetime('now')),
                is_sent      INTEGER NOT NULL DEFAULT 0
            )
        """)
        # Миграция существующей таблицы: добавляем новые колонки если их нет
        for col, definition in [
            ("cron_expr",    "TEXT"),
            ("is_recurring", "INTEGER NOT NULL DEFAULT 0"),
        ]:
            try:
                await db.execute(f"ALTER TABLE reminders ADD COLUMN {col} {definition}")
            except Exception:
                pass  # колонка уже существует
        await db.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                role        TEXT    NOT NULL,
                content     TEXT    NOT NULL,
                timestamp   TEXT    NOT NULL DEFAULT (datetime('now'))
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS memory (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL,
                content    TEXT    NOT NULL,
                embedding  BLOB,
                created_at TEXT    NOT NULL DEFAULT (datetime('now'))
            )
        """)
        await db.commit()


# ─── Reminders ────────────────────────────────────────────────────────────────

async def add_reminder(
    user_id: int,
    text: str,
    remind_at: datetime,
    cron_expr: str | None = None,
    is_recurring: bool = False,
) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO reminders (user_id, text, remind_at, cron_expr, is_recurring) VALUES (?, ?, ?, ?, ?)",
            (user_id, text, remind_at.isoformat(), cron_expr, int(is_recurring)),
        )
        await db.commit()
        return cursor.lastrowid


async def get_pending_reminders() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM reminders WHERE is_sent = 0"
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_user_reminders(user_id: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM reminders WHERE user_id = ? AND is_sent = 0 ORDER BY remind_at",
            (user_id,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def mark_reminder_sent(reminder_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE reminders SET is_sent = 1 WHERE id = ?", (reminder_id,)
        )
        await db.commit()


async def delete_reminder(reminder_id: int, user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM reminders WHERE id = ? AND user_id = ? AND is_sent = 0",
            (reminder_id, user_id),
        )
        await db.commit()
        return cursor.rowcount > 0


# ─── Chat History ─────────────────────────────────────────────────────────────

async def save_message(user_id: int, role: str, content: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO chat_history (user_id, role, content) VALUES (?, ?, ?)",
            (user_id, role, content),
        )
        await db.commit()


async def get_history(user_id: int, limit: int = 12) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT role, content FROM chat_history
               WHERE user_id = ?
               ORDER BY id DESC LIMIT ?""",
            (user_id, limit),
        )
        rows = await cursor.fetchall()
        return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]


# ─── API helpers ──────────────────────────────────────────────────────────────

async def get_all_messages(limit: int = 100, offset: int = 0) -> list[dict]:
    """Все сообщения из chat_history (для REST API)."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT id, user_id, role, content, timestamp
               FROM chat_history
               ORDER BY id DESC
               LIMIT ? OFFSET ?""",
            (limit, offset),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_stats() -> dict:
    """Базовая статистика для Dashboard."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Всего сообщений
        cur = await db.execute("SELECT COUNT(*) FROM chat_history")
        total_messages = (await cur.fetchone())[0]

        # Всего напоминаний
        cur = await db.execute("SELECT COUNT(*) FROM reminders")
        total_reminders = (await cur.fetchone())[0]

        # Активных напоминаний (не отправленных)
        cur = await db.execute("SELECT COUNT(*) FROM reminders WHERE is_sent = 0")
        active_reminders = (await cur.fetchone())[0]

        # Уникальных пользователей
        cur = await db.execute("SELECT COUNT(DISTINCT user_id) FROM chat_history")
        unique_users = (await cur.fetchone())[0]

    return {
        "total_messages": total_messages,
        "total_reminders": total_reminders,
        "active_reminders": active_reminders,
        "unique_users": unique_users,
    }


# ─── Reminders API (REST) ─────────────────────────────────────────────────────

async def get_all_active_reminders_api() -> list[dict]:
    """Все активные (не отправленные) напоминания для REST API."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT id, user_id, text AS message, remind_at AS next_run,
                      is_recurring, cron_expr, is_sent AS is_done, created_at
               FROM reminders
               ORDER BY remind_at ASC"""
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def delete_reminder_api(reminder_id: int) -> bool:
    """Удалить напоминание по ID (без проверки user_id — для REST API)."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM reminders WHERE id = ?",
            (reminder_id,),
        )
        await db.commit()
        return cursor.rowcount > 0


async def add_reminder_api(
    user_id: int,
    text: str,
    remind_at: datetime,
    cron_expr: str | None = None,
    is_recurring: bool = False,
) -> dict:
    """Создать напоминание через REST API. Возвращает созданную запись."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """INSERT INTO reminders (user_id, text, remind_at, cron_expr, is_recurring)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, text, remind_at.isoformat(), cron_expr, int(is_recurring)),
        )
        await db.commit()
        new_id = cursor.lastrowid
        db.row_factory = aiosqlite.Row
        cur2 = await db.execute(
            """SELECT id, user_id, text AS message, remind_at AS next_run,
                      is_recurring, cron_expr, is_sent AS is_done, created_at
               FROM reminders WHERE id = ?""",
            (new_id,),
        )
        row = await cur2.fetchone()
        return dict(row)


async def clear_history(user_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM chat_history WHERE user_id = ?", (user_id,))
        await db.commit()
