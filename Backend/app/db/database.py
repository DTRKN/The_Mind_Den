import aiosqlite
from datetime import datetime
from config import DB_PATH


async def create_tables() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
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


async def clear_history(user_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM chat_history WHERE user_id = ?", (user_id,))
        await db.commit()
