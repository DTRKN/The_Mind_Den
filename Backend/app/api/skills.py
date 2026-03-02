"""
api/skills.py
─────────────
CRUD для скиллов бота.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from skills.loader import reload_skills, get_loaded_skills

router = APIRouter(prefix="/api/skills", tags=["skills"])


class SkillCreateRequest(BaseModel):
    name: str
    title: str
    description: str
    content: str = ""


@router.get("")
async def list_skills():
    """Список загруженных скиллов."""
    return get_loaded_skills()


@router.post("", status_code=201)
async def create_skill(body: SkillCreateRequest):
    """Создать новый скилл (папка + SKILL.md) и перезагрузить кеш."""
    from agent.tools.skill_tool import SkillToolInput, run_skill_tool

    try:
        data = SkillToolInput(
            name=body.name,
            title=body.title,
            description=body.description,
            content=body.content,
        )
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

    result = await run_skill_tool(data)
    if not result.get("success"):
        raise HTTPException(
            status_code=500,
            detail=result.get("error", "Ошибка создания скилла"),
        )

    skills = get_loaded_skills()
    created = next((s for s in skills if s["name"] == data.name), result)
    return created
