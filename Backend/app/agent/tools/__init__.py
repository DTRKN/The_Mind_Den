"""
tools/__init__.py
─────────────────
OpenAI function-calling schemas для всех инструментов агента.
Реализации появятся в TASK-007, TASK-014, TASK-015, TASK-016.
"""

TOOL_SCHEMAS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "reminder_tool",
            "description": (
                "Управление напоминаниями пользователя. "
                "Создаёт разовые или повторяющиеся напоминания, "
                "возвращает список активных или удаляет по ID."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["create", "list", "delete"],
                        "description": "Действие: create — создать, list — список, delete — удалить",
                    },
                    "message": {
                        "type": "string",
                        "description": "Текст напоминания (для action=create)",
                    },
                    "datetime": {
                        "type": "string",
                        "description": "Дата и время в формате ISO 8601, например '2026-03-02T09:00:00' (для action=create)",
                    },
                    "recurring": {
                        "type": "boolean",
                        "description": "true — повторяющееся напоминание",
                    },
                    "cron_expr": {
                        "type": "string",
                        "description": "Cron-выражение для повторяющихся напоминаний, напр. '0 9 * * 1'",
                    },
                    "id": {
                        "type": "integer",
                        "description": "ID напоминания для удаления (для action=delete)",
                    },
                },
                "required": ["action"],
            },
        },
    },
]
