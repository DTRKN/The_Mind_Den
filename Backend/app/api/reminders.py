"""
api/reminders.py
────────────────
CRUD для напоминаний.
"""

from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from db.database import (
    get_all_active_reminders_api,
    add_reminder_api,
    delete_reminder_api,
)

router = APIRouter(prefix="/api/reminders", tags=["reminders"])


class ReminderCreateRequest(BaseModel):
    user_id: int = 0
    message: str
    next_run: str        # ISO datetime string, например "2026-03-01T15:00:00"
    is_recurring: bool = False
    cron_expr: str | None = None


@router.get("")
async def list_reminders():
    """Список всех активных напоминаний."""
    return await get_all_active_reminders_api()


@router.post("", status_code=201)
async def create_reminder(body: ReminderCreateRequest):
    """Создать напоминание через REST API."""
    try:
        remind_at = datetime.fromisoformat(body.next_run)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail="next_run: неверный формат. Ожидается ISO 8601, например 2026-03-01T15:00:00",
        )
    record = await add_reminder_api(
        user_id=body.user_id,
        text=body.message,
        remind_at=remind_at,
        cron_expr=body.cron_expr,
        is_recurring=body.is_recurring,
    )
    return record


@router.delete("/{reminder_id}", status_code=204)
async def delete_reminder(reminder_id: int):
    """Удалить напоминание по ID."""
    deleted = await delete_reminder_api(reminder_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Напоминание не найдено")
