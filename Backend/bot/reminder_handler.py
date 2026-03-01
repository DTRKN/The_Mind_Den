"""
reminder_handler.py
───────────────────
Обработка напоминаний: парсинг из текста, сохранение в БД,
отображение активных и отмена.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

from db.database import add_reminder, get_user_reminders, delete_reminder
from utils.parser import parse_reminder
from scheduler.scheduler import schedule_reminder


async def handle_reminder_text(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    text: str | None = None,
) -> None:
    """Вызывается когда в сообщении обнаружены триггеры напоминания."""
    user_id = update.effective_user.id
    # Принимаем текст либо как параметр (голосовой), либо из сообщения
    if text is None:
        text = update.message.text

    remind_at, reminder_text = parse_reminder(text)

    if not remind_at:
        await update.message.reply_text(
            "⏰ Не смог понять время. Попробуй:\n"
            "• _напомни в 17:30 съесть морковь_\n"
            "• _напомни завтра в 9:00 позвонить маме_\n"
            "• _напомни через 2 часа сделать кофе_",
            parse_mode="Markdown",
        )
        return

    if remind_at <= datetime.now():
        await update.message.reply_text(
            "❌ Указанное время уже в прошлом. Уточни время."
        )
        return

    reminder_id = await add_reminder(user_id, reminder_text, remind_at)
    await schedule_reminder(context.application, reminder_id, user_id, reminder_text, remind_at)

    time_str = remind_at.strftime("%d.%m.%Y в %H:%M")
    await update.message.reply_text(
        f"✅ Напоминание #{reminder_id} сохранено!\n"
        f"📌 *{reminder_text}*\n"
        f"🕐 {time_str}",
        parse_mode="Markdown",
    )


async def cmd_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/reminders — список активных напоминаний."""
    user_id = update.effective_user.id
    reminders = await get_user_reminders(user_id)

    if not reminders:
        await update.message.reply_text("📭 Активных напоминаний нет.")
        return

    lines = ["⏰ *Активные напоминания:*\n"]
    for r in reminders:
        dt = datetime.fromisoformat(r["remind_at"])
        time_str = dt.strftime("%d.%m.%Y %H:%M")
        lines.append(f"*#{r['id']}* — {r['text']} `[{time_str}]`")

    lines.append("\n_Для отмены: /cancel `<id>`_")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/cancel <id> — отменить напоминание."""
    user_id = update.effective_user.id
    args = context.args

    if not args or not args[0].isdigit():
        await update.message.reply_text("Использование: /cancel `<id>`", parse_mode="Markdown")
        return

    reminder_id = int(args[0])
    deleted = await delete_reminder(reminder_id, user_id)

    if deleted:
        await update.message.reply_text(f"🗑 Напоминание #{reminder_id} удалено.")
    else:
        await update.message.reply_text(
            f"❌ Напоминание #{reminder_id} не найдено или уже выполнено."
        )
