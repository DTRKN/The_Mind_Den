"""
reminder_tool.py
────────────────
Pydantic модель ReminderToolInput и функция run_reminder_tool.
Интегрируется в AgentRunner._dispatch().
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import logging
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, field_validator

logger = logging.getLogger(__name__)


class ReminderToolInput(BaseModel):
    action: Literal["create", "list", "delete"]
    message: Optional[str] = None       # текст напоминания
    datetime: Optional[str] = None      # ISO 8601
    recurring: Optional[bool] = False
    cron_expr: Optional[str] = None     # '0 8 * * *' — для повторяющихся
    id: Optional[int] = None            # для delete

    @field_validator("datetime", mode="before")
    @classmethod
    def validate_datetime(cls, v):
        if v is None:
            return v
        try:
            datetime.fromisoformat(str(v))
        except ValueError:
            raise ValueError(f"datetime должен быть в формате ISO 8601, получено: {v}")
        return v


async def run_reminder_tool(
    data: ReminderToolInput,
    user_id: int,
    app=None,
) -> dict:
    """
    Выполняет действие с напоминаниями.

    Returns:
        { "success": bool, "data": any }
    """
    from db.database import add_reminder, get_user_reminders, delete_reminder

    # ── create ────────────────────────────────────────────────────────────────
    if data.action == "create":
        if not data.datetime:
            return {"success": False, "error": "Не указано время (поле datetime)"}

        remind_at = datetime.fromisoformat(data.datetime)
        if remind_at <= datetime.now():
            return {"success": False, "error": "Указанное время уже в прошлом"}

        reminder_id = await add_reminder(
            user_id=user_id,
            text=data.message or "Напоминание",
            remind_at=remind_at,
            cron_expr=data.cron_expr,
            is_recurring=data.recurring or False,
        )
        logger.info(f"Создано напоминание #{reminder_id} для user {user_id}")

        if app:
            from scheduler.scheduler import schedule_reminder, schedule_recurring_reminder
            if data.recurring and data.cron_expr:
                await schedule_recurring_reminder(
                    app, reminder_id, user_id,
                    data.message or "Напоминание",
                    data.cron_expr,
                )
            else:
                await schedule_reminder(
                    app, reminder_id, user_id,
                    data.message or "Напоминание",
                    remind_at,
                )

        return {
            "success": True,
            "data": {
                "id": reminder_id,
                "message": data.message,
                "datetime": remind_at.isoformat(),
                "recurring": data.recurring,
                "cron_expr": data.cron_expr,
            },
        }

    # ── list ──────────────────────────────────────────────────────────────────
    if data.action == "list":
        reminders = await get_user_reminders(user_id)
        items = [
            {
                "id": r["id"],
                "message": r.get("text", ""),
                "remind_at": r.get("remind_at", ""),
                "is_recurring": bool(r.get("is_recurring", 0)),
                "cron_expr": r.get("cron_expr"),
            }
            for r in reminders
        ]
        return {"success": True, "data": items}

    # ── delete ────────────────────────────────────────────────────────────────
    if data.action == "delete":
        if not data.id:
            return {"success": False, "error": "Не указан id напоминания"}
        ok = await delete_reminder(data.id, user_id)
        # Убираем job из планировщика если есть
        try:
            from scheduler.scheduler import get_scheduler
            sched = get_scheduler()
            job_id = f"reminder_{data.id}"
            if sched.get_job(job_id):
                sched.remove_job(job_id)
        except Exception:
            pass
        return {"success": ok, "data": {"deleted_id": data.id}}

    return {"success": False, "error": f"Неизвестный action: {data.action}"}
