"""
skill_tool.py
─────────────
Инструмент агента для создания новых скиллов в файловой системе.

При вызове создаёт папку <skills_dir>/<name>/ и записывает в неё SKILL.md
с указанным содержимым, после чего перезагружает кеш скиллов.

Pydantic модель: SkillToolInput
Точка входа:    run_skill_tool(data) -> dict
"""

import logging
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from pathlib import Path
from pydantic import BaseModel, field_validator

logger = logging.getLogger(__name__)


class SkillToolInput(BaseModel):
    """Параметры для создания нового скилла."""

    name: str
    """Slug-имя скилла (используется как имя папки). Латиница, цифры, подчёркивания."""

    title: str
    """Заголовок скилла — попадает в строку '# Title' SKILL.md."""

    description: str
    """Краткое описание — попадает в строку '**Description:** ...'"""

    content: str = ""
    """Основное содержимое (инструкции, правила). Если пусто — создаётся только заголовок."""

    @field_validator("name")
    @classmethod
    def slugify_name(cls, v: str) -> str:
        slug = re.sub(r"[^\w\-]", "_", v.strip().lower())
        slug = re.sub(r"_+", "_", slug).strip("_")
        if not slug:
            raise ValueError("Имя скилла не может быть пустым")
        return slug


def _skills_base() -> Path:
    """Возвращает корневую директорию скиллов (рядом с папкой agent/)."""
    # __file__ = .../app/agent/tools/skill_tool.py
    # skills dir = .../app/skills/
    return Path(__file__).parent.parent.parent / "skills"


async def run_skill_tool(data: SkillToolInput) -> dict:
    """
    Создаёт папку skills/<name>/ и файл SKILL.md.

    После создания вызывает reload_skills() для обновления кеша.

    Returns:
        {"success": True, "name": ..., "path": ...}
        {"success": False, "error": ...}
    """
    skill_dir = _skills_base() / data.name
    skill_file = skill_dir / "SKILL.md"

    try:
        skill_dir.mkdir(parents=True, exist_ok=True)

        # Формируем содержимое SKILL.md
        lines = [
            f"# {data.title}",
            f"**Description:** {data.description}",
        ]
        if data.content.strip():
            lines.append("")
            lines.append(data.content.strip())

        skill_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
        logger.info(f"Скилл создан: [{data.name}] {data.title} → {skill_file}")

        # Перезагружаем кеш скиллов
        from skills.loader import reload_skills
        reload_skills()

        return {
            "success": True,
            "name": data.name,
            "title": data.title,
            "path": str(skill_file),
            "message": f"Скилл '{data.name}' создан и загружен.",
        }

    except Exception as e:
        logger.error(f"Ошибка создания скилла '{data.name}': {e}")
        return {"success": False, "error": str(e)}
