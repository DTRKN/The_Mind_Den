"""
tests/conftest.py
─────────────────
Общие фикстуры pytest.
"""

import sys
import os
import asyncio
import tempfile
import pytest
import pytest_asyncio

# Добавляем app/ в path — тесты запускаются из Backend/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from httpx import AsyncClient, ASGITransport
from api.app import create_app


@pytest.fixture(scope="session")
def event_loop():
    """Один event loop на всю сессию тестов."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def db_path(tmp_path_factory):
    """Временная БД для тестов (не трогает боевую)."""
    tmp = tmp_path_factory.mktemp("data")
    path = str(tmp / "test.db")
    # Устанавливаем переменную окружения до импорта database
    os.environ["DB_PATH"] = path
    import db.database as _db
    _db.DB_PATH = path  # type: ignore[attr-defined]
    await _db.create_tables()
    return path


@pytest_asyncio.fixture(scope="session")
async def client(db_path):
    """HTTP-клиент для тестирования FastAPI."""
    app = create_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
