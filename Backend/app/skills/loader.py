"""
loader.py
─────────
Загрузчик скиллов из файловой системы.

Структура скиллов:
    skills/
        <skill_name>/
            SKILL.md   ← обязательный файл с описанием скилла

Формат SKILL.md:
    # Название скилла
    **Description:** Краткое описание что делает скилл

    ## Инструкции
    Подробный текст, промпт, правила...

Загрузчик читает все SKILL.md рекурсивно и возвращает объединённый текст
для инъекции в system prompt AgentRunner.

Использование:
    from skills.loader import reload_skills, get_skills_text
    reload_skills()          # при старте приложения
    text = get_skills_text() # получить кешированный текст
"""

import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

# ─── Глобальный кеш ────────────────────────────────────────────────────────────
_skills_text: str = ""
_loaded_skills: list[dict] = []  # [{"name": ..., "description": ..., "content": ...}]


# ─── Путь по умолчанию ─────────────────────────────────────────────────────────
def _default_skills_dir() -> Path:
    """Возвращает путь к директории skills рядом с loader.py."""
    return Path(__file__).parent


# ─── Парсинг SKILL.md ─────────────────────────────────────────────────────────

def _parse_skill_file(path: Path) -> dict | None:
    """
    Читает SKILL.md и возвращает dict с полями:
      name        — имя папки (= имя скилла)
      description — первая строка с **Description:** или заголовок # ...
      content     — полный текст файла
    """
    try:
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            return None

        # Имя скилла = имя папки
        skill_name = path.parent.name

        # Пытаемся извлечь описание
        description = skill_name
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("# "):
                description = line[2:].strip()
                break
            if "**Description:**" in line or "**Описание:**" in line:
                desc_part = (
                    line.replace("**Description:**", "")
                    .replace("**Описание:**", "")
                    .strip()
                )
                if desc_part:
                    description = desc_part
                break

        return {
            "name": skill_name,
            "description": description,
            "content": text,
            "path": str(path),
        }
    except Exception as e:
        logger.error(f"Ошибка чтения скилла {path}: {e}")
        return None


# ─── Основная функция загрузки ────────────────────────────────────────────────

def reload_skills(skills_dir: str | Path | None = None) -> list[dict]:
    """
    Читает все SKILL.md из skills_dir/* и обновляет глобальный кеш.

    Args:
        skills_dir: путь к директории со скиллами.
                    По умолчанию — Backend/app/skills/

    Returns:
        Список загруженных скиллов (list[dict]).
    """
    global _skills_text, _loaded_skills

    base = Path(skills_dir) if skills_dir else _default_skills_dir()

    if not base.exists():
        logger.warning(f"Skills директория не найдена: {base}")
        _loaded_skills = []
        _skills_text = ""
        return []

    skills: list[dict] = []

    for skill_dir in sorted(base.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            continue
        parsed = _parse_skill_file(skill_file)
        if parsed:
            skills.append(parsed)
            logger.info(f"Скилл загружен: [{parsed['name']}] {parsed['description']}")

    _loaded_skills = skills
    _skills_text = _build_skills_text(skills)

    if skills:
        logger.info(f"Загружено скиллов: {len(skills)}")
    else:
        logger.info("Скиллов не найдено (папка пуста или нет SKILL.md)")

    return skills


def _build_skills_text(skills: list[dict]) -> str:
    """Формирует единый текст из списка скиллов для инъекции в system prompt."""
    if not skills:
        return ""

    parts = []
    for skill in skills:
        parts.append(f"### Скилл: {skill['name']}\n{skill['content']}")

    return "\n\n".join(parts)


# ─── Геттеры (используются в handlers.py) ─────────────────────────────────────

def get_skills_text() -> str:
    """Возвращает кешированный текст скиллов для system prompt."""
    return _skills_text


def get_loaded_skills() -> list[dict]:
    """Возвращает список загруженных скиллов (для /api/skills)."""
    return list(_loaded_skills)
