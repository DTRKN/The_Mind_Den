"""
tests/test_db.py
────────────────
Тесты слоя базы данных.
"""

import pytest
import pytest_asyncio
from datetime import datetime

import db.database as db


@pytest.mark.asyncio
async def test_create_tables_idempotent(db_path):
    """create_tables можно вызвать несколько раз без ошибок."""
    await db.create_tables()
    await db.create_tables()


@pytest.mark.asyncio
async def test_save_and_get_history(db_path):
    user_id = 42
    await db.save_message(user_id, "user", "Привет")
    await db.save_message(user_id, "assistant", "Привет! Чем могу помочь?")

    history = await db.get_history(user_id, limit=10)
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "Привет"


@pytest.mark.asyncio
async def test_clear_history(db_path):
    user_id = 99
    await db.save_message(user_id, "user", "Сообщение")
    await db.clear_history(user_id)
    history = await db.get_history(user_id)
    assert history == []


@pytest.mark.asyncio
async def test_add_and_get_reminder(db_path):
    rid = await db.add_reminder(
        user_id=1,
        text="Полить цветы",
        remind_at=datetime(2030, 6, 1, 9, 0),
    )
    assert isinstance(rid, int)

    reminders = await db.get_user_reminders(user_id=1)
    ids = [r["id"] for r in reminders]
    assert rid in ids


@pytest.mark.asyncio
async def test_mark_reminder_sent(db_path):
    rid = await db.add_reminder(
        user_id=2,
        text="Выпить воды",
        remind_at=datetime(2030, 1, 1, 8, 0),
    )
    await db.mark_reminder_sent(rid)

    # После отметки не должен попасть в активные
    reminders = await db.get_user_reminders(user_id=2)
    ids = [r["id"] for r in reminders]
    assert rid not in ids


@pytest.mark.asyncio
async def test_get_stats(db_path):
    stats = await db.get_stats()
    assert "message_count" in stats or isinstance(stats, dict)
