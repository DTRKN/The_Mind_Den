"""
file_tool.py
────────────
Инструмент для работы с файлами в изолированной директории WORKSPACE_DIR.

Операции:
  read   — прочитать содержимое файла
  write  — создать или перезаписать файл
  list   — вывести список файлов/папок

Безопасность:
  Все пути разрешаются через os.path.realpath() и проверяются на то,
  что они начинаются с realpath(WORKSPACE_DIR).
  Любая попытка выйти за пределы workspace (path traversal, /etc/passwd и т.д.)
  немедленно отклоняется с ошибкой.

Использование:
    from agent.tools.file_tool import FileToolInput, run_file_tool
    result = await run_file_tool(FileToolInput(action="write", path="notes.txt", content="hello"))
"""

import logging
import os
from typing import Literal, Optional

from pydantic import BaseModel, Field

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import WORKSPACE_DIR

logger = logging.getLogger(__name__)


# ─── Pydantic модель ───────────────────────────────────────────────────────────


class FileToolInput(BaseModel):
    """Входные параметры для file_tool."""

    action: Literal["read", "write", "list"] = Field(
        description="read — прочитать файл, write — записать файл, list — список содержимого папки"
    )
    path: str = Field(
        default=".",
        description="Относительный путь внутри workspace (например 'notes.txt' или 'folder/')",
    )
    content: Optional[str] = Field(
        default=None,
        description="Содержимое для записи в файл (только для action=write)",
    )


# ─── Утилиты изоляции путей ────────────────────────────────────────────────────


def _get_workspace() -> str:
    """Возвращает абсолютный realpath рабочей директории, создаёт её при необходимости."""
    workspace = os.path.realpath(os.path.abspath(WORKSPACE_DIR))
    os.makedirs(workspace, exist_ok=True)
    return workspace


def _safe_resolve(user_path: str) -> str | None:
    """
    Разрешает пользовательский путь относительно workspace.
    Возвращает None, если путь выходит за пределы workspace.
    """
    workspace = _get_workspace()

    # Явный отказ для абсолютных путей (Unix /etc/... и Windows C:\\...)
    if os.path.isabs(user_path):
        logger.warning(f"Absolute path blocked: '{user_path}'")
        return None

    # Нормализуем: убираем ведущий / чтобы os.path.join не сбрасывал workspace
    normalized = user_path.lstrip("/\\")
    candidate = os.path.realpath(os.path.join(workspace, normalized))
    # Защита от path traversal
    if not candidate.startswith(workspace + os.sep) and candidate != workspace:
        logger.warning(f"Path traversal attempt blocked: '{user_path}' → '{candidate}'")
        return None
    return candidate


# ─── Операции ─────────────────────────────────────────────────────────────────


def _read_file(path: str) -> dict:
    resolved = _safe_resolve(path)
    if resolved is None:
        return {"success": False, "error": "Доступ запрещён: путь выходит за пределы workspace"}

    if not os.path.exists(resolved):
        return {"success": False, "error": f"Файл не найден: {path}"}

    if os.path.isdir(resolved):
        return {"success": False, "error": f"'{path}' — это директория, а не файл. Используй action=list"}

    try:
        with open(resolved, "r", encoding="utf-8") as f:
            content = f.read()
        return {"success": True, "path": path, "content": content}
    except Exception as e:
        return {"success": False, "error": f"Ошибка чтения: {e}"}


def _write_file(path: str, content: str) -> dict:
    if not content and content != "":
        return {"success": False, "error": "Поле 'content' обязательно для action=write"}

    resolved = _safe_resolve(path)
    if resolved is None:
        return {"success": False, "error": "Доступ запрещён: путь выходит за пределы workspace"}

    try:
        os.makedirs(os.path.dirname(resolved), exist_ok=True)
        with open(resolved, "w", encoding="utf-8") as f:
            f.write(content)
        return {"success": True, "path": path, "bytes_written": len(content.encode("utf-8"))}
    except Exception as e:
        return {"success": False, "error": f"Ошибка записи: {e}"}


def _list_dir(path: str) -> dict:
    resolved = _safe_resolve(path)
    if resolved is None:
        return {"success": False, "error": "Доступ запрещён: путь выходит за пределы workspace"}

    if not os.path.exists(resolved):
        return {"success": False, "error": f"Путь не найден: {path}"}

    if not os.path.isdir(resolved):
        return {"success": False, "error": f"'{path}' — это файл. Используй action=read"}

    try:
        entries = []
        for name in sorted(os.listdir(resolved)):
            full = os.path.join(resolved, name)
            entries.append({
                "name": name,
                "type": "dir" if os.path.isdir(full) else "file",
                "size": os.path.getsize(full) if os.path.isfile(full) else None,
            })
        return {"success": True, "path": path, "entries": entries, "count": len(entries)}
    except Exception as e:
        return {"success": False, "error": f"Ошибка чтения директории: {e}"}


# ─── Основная точка входа ──────────────────────────────────────────────────────


async def run_file_tool(data: FileToolInput) -> dict:
    """Диспетчер: маршрутизирует вызов к нужной операции."""
    logger.info(f"file_tool: action={data.action}, path={data.path!r}")

    if data.action == "read":
        return _read_file(data.path)

    if data.action == "write":
        if data.content is None:
            return {"success": False, "error": "Поле 'content' обязательно для action=write"}
        return _write_file(data.path, data.content)

    if data.action == "list":
        return _list_dir(data.path)

    return {"success": False, "error": f"Неизвестный action: {data.action}"}
