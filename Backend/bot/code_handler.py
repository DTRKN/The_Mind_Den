"""
code_handler.py
───────────────
Copilot-режим: пользователь описывает задачу на естественном языке,
AI сам решает какие файлы создать/прочитать/изменить в проекте.

Доступные инструменты (tools):
  • read_file        — прочитать файл
  • write_file       — записать / создать файл
  • list_directory   — список файлов в папке
  • run_git_command  — выполнить git-команду (add / commit / status)
"""

import json
import os
import subprocess
from typing import Any

from openai import AsyncOpenAI
from config import (
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    PROJECT_ROOT,
)
from bot.ai_handler import get_model, _build_system_code

# ─── Определения инструментов для OpenRouter ──────────────────────────────────

CODE_TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Читает содержимое файла из проекта",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Относительный путь файла от корня проекта, например src/pages/Home.tsx",
                    }
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Создаёт новый файл или полностью перезаписывает существующий",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Относительный путь от корня проекта",
                    },
                    "content": {
                        "type": "string",
                        "description": "Полное содержимое файла",
                    },
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "Возвращает список файлов и папок по указанному пути",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Относительный путь от корня проекта. Используй '.' для корня.",
                    }
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_git_command",
            "description": "Выполняет git-команду в корне проекта (только add, status, log, diff, commit)",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Git-команда, например: 'add .' или 'commit -m \"feat: add new page\"' или 'status'",
                    }
                },
                "required": ["command"],
            },
        },
    },
]


# ─── Исполнение инструментов локально ─────────────────────────────────────────

def _safe_path(relative_path: str) -> str:
    """Преобразует относительный путь в абсолютный, защищая от path traversal."""
    abs_path = os.path.normpath(os.path.join(PROJECT_ROOT, relative_path))
    if not abs_path.startswith(os.path.normpath(PROJECT_ROOT)):
        raise ValueError(f"Доступ запрещён: путь выходит за пределы проекта ({abs_path})")
    return abs_path


def _execute_tool(name: str, args: dict) -> str:
    """Выполняет инструмент и возвращает строку результата."""
    try:
        if name == "read_file":
            abs_path = _safe_path(args["path"])
            if not os.path.exists(abs_path):
                return f"❌ Файл не найден: {args['path']}"
            with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            if len(content) > 8000:
                content = content[:8000] + "\n... [файл обрезан, показаны первые 8000 символов]"
            return content

        elif name == "write_file":
            abs_path = _safe_path(args["path"])
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(args["content"])
            return f"✅ Файл записан: {args['path']}"

        elif name == "list_directory":
            abs_path = _safe_path(args["path"])
            if not os.path.exists(abs_path):
                return f"❌ Папка не найдена: {args['path']}"
            items = []
            for item in sorted(os.listdir(abs_path)):
                full = os.path.join(abs_path, item)
                items.append(f"{'📁' if os.path.isdir(full) else '📄'} {item}")
            return "\n".join(items) if items else "(пусто)"

        elif name == "run_git_command":
            cmd = args["command"].strip()
            # Разрешаем только безопасные команды
            allowed = ("status", "log", "diff", "add", "commit")
            if not any(cmd.startswith(a) for a in allowed):
                return f"❌ Команда не разрешена. Доступны: {', '.join(allowed)}"
            result = subprocess.run(
                ["git"] + cmd.split(),
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=15,
            )
            output = result.stdout or result.stderr
            return output.strip() or "(пустой вывод)"

        else:
            return f"❌ Неизвестный инструмент: {name}"

    except Exception as e:
        return f"❌ Ошибка при выполнении {name}: {e}"


# ─── Основная функция code assistant ──────────────────────────────────────────

async def code_chat(user_message: str) -> str:
    """
    Запрос к AI с tool calling.
    Возвращает финальный ответ в виде строки.
    """
    client = AsyncOpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url=OPENROUTER_BASE_URL,
    )
    model = get_model()

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": _build_system_code()},
        {"role": "user", "content": user_message},
    ]

    # Цикл: отправляем запрос → AI вызывает инструменты → выполняем → повторяем
    for _ in range(10):  # максимум 10 итераций tool calls
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            tools=CODE_TOOLS,
            tool_choice="auto",
            max_tokens=4096,
        )

        message = response.choices[0].message

        # Если AI не вызвал ни одного инструмента — возвращаем финальный ответ
        if not message.tool_calls:
            return message.content or "(нет ответа)"

        # Добавляем ответ ассистента с вызовами в историю
        messages.append({
            "role": "assistant",
            "content": message.content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in message.tool_calls
            ],
        })

        # Выполняем каждый инструмент и добавляем результат
        for tc in message.tool_calls:
            args = json.loads(tc.function.arguments)
            result = _execute_tool(tc.function.name, args)
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result,
            })

    return "⚠️ Превышен лимит итераций. Попробуй уточнить задачу."
