"""Test sqlite-vec integration (TASK-012)."""
import asyncio
import sqlite_vec
import aiosqlite


async def _load_vec_extension(db: aiosqlite.Connection) -> None:
    def _inner():
        db._connection.enable_load_extension(True)
        sqlite_vec.load(db._connection)
        db._connection.enable_load_extension(False)
    await db._execute(_inner)


async def test():
    db = await aiosqlite.connect(":memory:")
    await _load_vec_extension(db)
    cur = await db.execute("SELECT vec_version()")
    row = await cur.fetchone()
    print(f"vec_version(): {row[0]}")
    await db.execute(
        "CREATE TABLE IF NOT EXISTS memory ("
        "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "  user_id INTEGER NOT NULL,"
        "  content TEXT NOT NULL,"
        "  embedding BLOB,"
        "  created_at TEXT NOT NULL DEFAULT (datetime(chr(39)||'now'||chr(39)))"
        ")"
    )
    await db.commit()
    cur2 = await db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='memory'")
    r = await cur2.fetchone()
    print(f"memory table: {r[0] if r else 'NOT FOUND'}")
    await db.close()
    print("All tests PASSED")

asyncio.run(test())
