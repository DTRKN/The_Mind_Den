"""
agent.py
────────
AgentRunner — единый цикл выполнения запросов к OpenRouter с поддержкой tool_calls.

Цикл:
  1. Формирует messages (system prompt + история + новое сообщение)
  2. Отправляет запрос в OpenRouter с tool schemas
  3. Если модель вернула tool_call → вызывает _dispatch() → добавляет tool result
  4. Повторяет до финального ответа или лимита итераций
  5. Сохраняет user/assistant в историю и возвращает текст
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import logging
from datetime import datetime

from openai import AsyncOpenAI
from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_MODEL
from db.database import get_history, save_message
from agent.system_prompt import build_system_prompt
from agent.tools import TOOL_SCHEMAS

logger = logging.getLogger(__name__)

# Модель — может меняться через /model (shared state)
_current_model: str = OPENROUTER_MODEL


def get_model() -> str:
    return _current_model


def set_model(name: str) -> None:
    global _current_model
    _current_model = name


class AgentRunner:
    """
    Запускает цикл OpenRouter + tools для одного сообщения пользователя.

    Args:
        app: экземпляр telegram.ext.Application (нужен для schedule_reminder)
        skills_text: текст загруженных скиллов для инъекции в system prompt
    """

    MAX_ITERATIONS = 5

    def __init__(self, app=None, skills_text: str = "") -> None:
        self.app = app
        self.skills_text = skills_text
        self._client = AsyncOpenAI(
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL,
        )

    async def run(self, user_id: int, message: str) -> str:
        """Выполняет агентный цикл и возвращает итоговый текст ответа."""
        history = await get_history(user_id, limit=20)

        messages: list[dict] = [
            {"role": "system", "content": build_system_prompt(self.skills_text)},
            *history,
            {"role": "user", "content": message},
        ]

        for iteration in range(self.MAX_ITERATIONS):
            try:
                response = await self._client.chat.completions.create(
                    model=_current_model,
                    messages=messages,
                    tools=TOOL_SCHEMAS,
                    tool_choice="auto",
                    max_tokens=2048,
                )
            except Exception as e:
                logger.error(f"OpenRouter error: {e}")
                return "Произошла ошибка при обращении к AI. Попробуй ещё раз."

            choice = response.choices[0]
            msg = choice.message

            # Нет tool_calls → финальный ответ
            if not msg.tool_calls:
                reply = (msg.content or "").strip()
                await save_message(user_id, "user", message)
                await save_message(user_id, "assistant", reply)
                return reply

            # Добавляем assistant-сообщение с tool_calls в цепочку
            messages.append(self._serialize_assistant_message(msg))

            # Вызываем каждый инструмент
            for tc in msg.tool_calls:
                logger.info(f"Tool call: {tc.function.name}({tc.function.arguments[:120]})")
                result = await self._dispatch(user_id, tc.function.name, tc.function.arguments)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result, ensure_ascii=False, default=str),
                })

            logger.debug(f"AgentRunner iteration {iteration + 1}/{self.MAX_ITERATIONS}")

        # Защита от бесконечного цикла
        fallback = "Не удалось завершить задачу за допустимое число шагов."
        await save_message(user_id, "user", message)
        await save_message(user_id, "assistant", fallback)
        return fallback

    # ─── Сериализация ──────────────────────────────────────────────────────────

    @staticmethod
    def _serialize_assistant_message(msg) -> dict:
        """Конвертирует объект assistant-сообщения в plain dict для messages list."""
        tool_calls = []
        for tc in (msg.tool_calls or []):
            tool_calls.append({
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            })
        result = {"role": "assistant", "content": msg.content or ""}
        if tool_calls:
            result["tool_calls"] = tool_calls
        return result

    # ─── Диспетчер инструментов ────────────────────────────────────────────────

    async def _dispatch(self, user_id: int, tool_name: str, arguments_str: str) -> dict:
        """Маршрутизирует вызов инструмента к нужной реализации."""
        try:
            args = json.loads(arguments_str)
        except Exception:
            return {"success": False, "error": "invalid JSON in arguments"}

        handlers = {
            "reminder_tool": self._handle_reminder,
        }

        handler = handlers.get(tool_name)
        if handler is None:
            logger.warning(f"Unknown tool: {tool_name}")
            return {"success": False, "error": f"tool '{tool_name}' not implemented yet"}

        try:
            return await handler(user_id, args)
        except Exception as e:
            logger.error(f"Tool {tool_name} error: {e}")
            return {"success": False, "error": str(e)}

    # ─── Реализации инструментов ───────────────────────────────────────────────

    async def _handle_reminder(self, user_id: int, args: dict) -> dict:
        """reminder_tool: create / list / delete."""
        from db.database import (
            add_reminder,
            get_user_reminders,
            delete_reminder,
        )

        action = args.get("action")

        if action == "create":
            message = args.get("message", "Напоминание")
            datetime_str = args.get("datetime")
            if not datetime_str:
                return {"success": False, "error": "Не указано время напоминания (datetime)"}

            try:
                remind_at = datetime.fromisoformat(datetime_str)
            except ValueError:
                return {"success": False, "error": f"Неверный формат datetime: {datetime_str}"}

            if remind_at <= datetime.now():
                return {"success": False, "error": "Указанное время уже в прошлом"}

            reminder_id = await add_reminder(user_id, message, remind_at)

            if self.app:
                from scheduler.scheduler import schedule_reminder
                await schedule_reminder(self.app, reminder_id, user_id, message, remind_at)

            return {
                "success": True,
                "data": {
                    "id": reminder_id,
                    "message": message,
                    "datetime": remind_at.isoformat(),
                },
            }

        if action == "list":
            reminders = await get_user_reminders(user_id)
            # Конвертируем в простые dict для JSON
            data = [
                {
                    "id": r["id"],
                    "message": r.get("text", r.get("message", "")),
                    "remind_at": r.get("remind_at", ""),
                }
                for r in reminders
            ]
            return {"success": True, "data": data}

        if action == "delete":
            rid = args.get("id")
            if not rid:
                return {"success": False, "error": "Не указан id напоминания"}
            ok = await delete_reminder(int(rid), user_id)
            return {"success": ok, "data": None}

        return {"success": False, "error": f"Неизвестный action: {action}"}
