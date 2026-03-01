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
    {
        "type": "function",
        "function": {
            "name": "memory_tool",
            "description": (
                "Долгосрочная память агента на базе Pinecone. "
                "Сохраняет важную информацию о пользователе, "
                "ищет релевантные воспоминания по смысловому запросу, "
                "или возвращает список всех сохранённых фактов."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["save", "search", "list"],
                        "description": "save — сохранить факт, search — найти по запросу, list — все воспоминания",
                    },
                    "content": {
                        "type": "string",
                        "description": (
                            "Текст факта для сохранения (action=save) "
                            "или поисковый запрос (action=search)"
                        ),
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Максимальное число результатов (action=search или action=list), по умолчанию 5",
                    },
                },
                "required": ["action"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "file_tool",
            "description": (
                "Работа с файлами в изолированной рабочей директории (workspace). "
                "Читает, создаёт/перезаписывает файлы и выводит список содержимого папки. "
                "Операции за пределами workspace запрещены."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["read", "write", "list"],
                        "description": "read — прочитать файл, write — записать файл, list — список содержимого папки",
                    },
                    "path": {
                        "type": "string",
                        "description": "Относительный путь внутри workspace, например 'notes.txt' или 'docs/'",
                    },
                    "content": {
                        "type": "string",
                        "description": "Содержимое файла (только для action=write)",
                    },
                },
                "required": ["action"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "skill_tool",
            "description": (
                "Создаёт новый скилл: генерирует папку и SKILL.md в директории скиллов. "
                "Используй, когда пользователь просит обучить боту новому навыку или создать инструкцию."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Slug-имя скилла (латиница, цифры, подчёркивания), например 'translate_japanese'",
                    },
                    "title": {
                        "type": "string",
                        "description": "Заголовок скилла на человеческом языке, например 'Перевод на японский'",
                    },
                    "description": {
                        "type": "string",
                        "description": "Одна строка: краткое описание что делает скилл",
                    },
                    "content": {
                        "type": "string",
                        "description": "Подробные инструкции, правила, промпт — основное тело SKILL.md",
                    },
                },
                "required": ["name", "title", "description"],
            },
        },
    },
]
