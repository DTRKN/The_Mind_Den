"""
tests/test_api.py
─────────────────
Тесты REST API эндпоинтов.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_simple(client: AsyncClient):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_health_detailed(client: AsyncClient):
    r = await client.get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert "status" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_stats(client: AsyncClient):
    r = await client.get("/api/stats")
    assert r.status_code == 200
    data = r.json()
    assert "uptime_seconds" in data


@pytest.mark.asyncio
async def test_messages_empty(client: AsyncClient):
    r = await client.get("/api/messages")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_reminders_list(client: AsyncClient):
    r = await client.get("/api/reminders")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_reminder_create_and_delete(client: AsyncClient):
    # Создаём
    payload = {
        "user_id": 1,
        "message": "Тест напоминания",
        "next_run": "2030-01-01T12:00:00",
        "is_recurring": False,
    }
    r = await client.post("/api/reminders", json=payload)
    assert r.status_code == 201
    created = r.json()
    assert "id" in created

    # Проверяем что появился в списке
    r = await client.get("/api/reminders")
    ids = [x["id"] for x in r.json()]
    assert created["id"] in ids

    # Удаляем
    r = await client.delete(f"/api/reminders/{created['id']}")
    assert r.status_code == 204

    # Проверяем что исчез
    r = await client.get("/api/reminders")
    ids = [x["id"] for x in r.json()]
    assert created["id"] not in ids


@pytest.mark.asyncio
async def test_reminder_delete_not_found(client: AsyncClient):
    r = await client.delete("/api/reminders/999999")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_reminder_bad_date(client: AsyncClient):
    r = await client.post("/api/reminders", json={
        "user_id": 1,
        "message": "Тест",
        "next_run": "не-дата",
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_skills_list(client: AsyncClient):
    r = await client.get("/api/skills")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
