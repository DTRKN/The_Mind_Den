"""
handlers.py
───────────
Точка роутинга всех входящих сообщений:
  • Whitelist: только ALLOWED_USER_IDS могут пользоваться ботом
  • /start, /help   — приветствие
  • /model <name>   — смена AI-модели
  • /models         — список популярных моделей
  • /code           — переключение в code-assistant режим
  • /chat           — переключение в обычный AI-чат
  • /reminders      — список напоминаний
  • /cancel <id>    — удалить напоминание
  • /clear          — очистить историю чата
  • Голосовые       — транскрипция через Groq → роутинг как текст
  • Текст           — напоминание | code-запрос | AI-чат
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import logging
from functools import wraps

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from datetime import datetime

from config import ALLOWED_USER_IDS
from bot.ai_handler import POPULAR_MODELS
from bot.code_handler import code_chat
from bot.reminder_handler import cmd_reminders, cmd_cancel
from bot.voice_handler import transcribe_voice
from db.database import clear_history
from agent.agent import AgentRunner, get_model, set_model
from skills.loader import get_skills_text

logger = logging.getLogger(__name__)

# ─── Режимы пользователя (хранятся в context.user_data) ──────────────────────
MODE_CHAT = "chat"
MODE_CODE = "code"

# ─── Whitelist декоратор ───────────────────────────────────────────────────────

def whitelist_only(func):
    """Декоратор: отклоняет запросы от пользователей не из whitelist."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if ALLOWED_USER_IDS and user_id not in ALLOWED_USER_IDS:
            logger.warning(f"Отклонён доступ для user_id={user_id}")
            await update.message.reply_text("🚫 Доступ запрещён.")
            return
        return await func(update, context)
    return wrapper


# ─── Команды ──────────────────────────────────────────────────────────────────

@whitelist_only
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["mode"] = MODE_CHAT
    await update.message.reply_text("Привет! Чем могу помочь?")


@whitelist_only
async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Привет! Чем могу помочь?")


@whitelist_only
async def cmd_code_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["mode"] = MODE_CODE
    await update.message.reply_text("Режим работы с кодом. Для обычного чата: /chat")


@whitelist_only
async def cmd_chat_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["mode"] = MODE_CHAT
    await update.message.reply_text("💬 Режим обычного чата активирован.")


@whitelist_only
async def cmd_model(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if not args:
        await update.message.reply_text(
            f"Текущая модель: `{get_model()}`\n\nДля смены: /model `<name>`\nСписок: /models",
            parse_mode="Markdown",
        )
        return
    new_model = args[0].strip()
    set_model(new_model)
    await update.message.reply_text(f"✅ Модель изменена на: `{new_model}`", parse_mode="Markdown")


@whitelist_only
async def cmd_models(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lines = ["📋 *Популярные модели OpenRouter:*\n"]
    for model_id, desc in POPULAR_MODELS:
        lines.append(f"• `{model_id}`\n  _{desc}_")
    lines.append(f"\n*Текущая:* `{get_model()}`")
    lines.append("Для смены: /model `<model_id>`")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


@whitelist_only
async def cmd_clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await clear_history(update.effective_user.id)
    await update.message.reply_text("🗑 История чата очищена.")


@whitelist_only
async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from db.database import get_user_reminders
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    mode = context.user_data.get("mode", MODE_CHAT)
    reminders = await get_user_reminders(update.effective_user.id)
    await update.message.reply_text(
        f"🤖 *Статус бота*\n\n"
        f"🕐 Время сервера: `{now}`\n"
        f"🧠 Модель: `{get_model()}`\n"
        f"💬 Режим: `{mode}`\n"
        f"⏰ Активных напоминаний: `{len(reminders)}`",
        parse_mode="Markdown",
    )


# ─── Обработчики сообщений ─────────────────────────────────────────────────────

@whitelist_only
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Роутер текстовых сообщений."""
    await _process_text(update, context, update.message.text)


async def _process_text(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    """Основная логика обработки текста (используется и для голосовых)."""
    mode = context.user_data.get("mode", MODE_CHAT)

    # Code assistant режим (legacy)
    if mode == MODE_CODE:
        await update.message.chat.send_action("typing")
        reply = await code_chat(text)
        for chunk in _split_message(reply):
            await update.message.reply_text(chunk, parse_mode="Markdown")
        return

    # AgentRunner — единый цикл: сам решает какие tools вызвать
    await update.message.chat.send_action("typing")
    runner = AgentRunner(app=context.application, skills_text=get_skills_text())
    reply = await runner.run(update.effective_user.id, text)
    for chunk in _split_message(reply):
        await update.message.reply_text(chunk, parse_mode="Markdown")


@whitelist_only
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Роутер голосовых сообщений: транскрипция → handle_text."""
    text = await transcribe_voice(update, context)
    if not text:
        await update.message.reply_text("❌ Не удалось распознать речь.")
        return

    await update.message.reply_text(f"📝 *Распознано:* _{text}_", parse_mode="Markdown")

    # Обрабатываем транскрибированный текст напрямую
    await _process_text(update, context, text)


# ─── Регистрация обработчиков ──────────────────────────────────────────────────

def register_handlers(app: Application) -> None:
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("code", cmd_code_mode))
    app.add_handler(CommandHandler("chat", cmd_chat_mode))
    app.add_handler(CommandHandler("model", cmd_model))
    app.add_handler(CommandHandler("models", cmd_models))
    app.add_handler(CommandHandler("reminders", cmd_reminders))
    app.add_handler(CommandHandler("cancel", cmd_cancel))
    app.add_handler(CommandHandler("clear", cmd_clear))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))


# ─── Утилиты ──────────────────────────────────────────────────────────────────

def _split_message(text: str, max_len: int = 4000) -> list[str]:
    """Разбивает длинный текст на части для Telegram."""
    if len(text) <= max_len:
        return [text]
    parts = []
    while text:
        parts.append(text[:max_len])
        text = text[max_len:]
    return parts
