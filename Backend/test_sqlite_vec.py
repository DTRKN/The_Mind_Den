"""Тест интеграции sqlite-vec (TASK-012)."""
import asyncio
import sqlite_vec
import aiosqlite


async def _load_vec_extension(db: aiosqlite.Connection) -> None:
    """Загружает sqlite-vec внутри потока aiosqlite (thread-safe)."""
    def _inner():
        db._connection.enable_load_extension(True)  # type: ignore
        sqlite_vec.load(db._connection)  # type: ignore
        db._connection.enable_load_extension(False)  # type: ignore
    await db._execute(_inner)  # type: ignore


async def test():
    db = await aiosqlite.connect(":memory:")

    # 1. Загружаем расширение (thread-safe)
    await _load_vec_extension(db)

    # 2. Проверяем vec_version()
    cur = await db.execute("SELECT vec_version()")
    row = await cur.fetchone()
    print(f"vec_version(): {row[0]}")

    # 3. Создаём таблицу memory
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS memory (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            content    TEXT    NOT NULL,
            embedding  BLOB,
            created_at TEXT    NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    await db.commit()
    print("memory table: OK")

    # 4. Проверяем таблицу
    cur2 = await db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='memory'")
    r = await cur2.fetchone()
    print(f"table in sqlite_master: {r[0] if r else 'NOT FOUND'}")

    await db.close()
    print("All tests PASSED")


asyncio.run(test())
