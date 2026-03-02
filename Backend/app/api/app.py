"""
api/app.py
──────────
FastAPI-приложение: только роутеры, без lifespan бота.
Создается один раз и передаётся в uvicorn.Server из main.py.
"""

from fastapi import FastAPI

from api.health import router as health_router
from api.messages import router as messages_router
from api.reminders import router as reminders_router
from api.skills import router as skills_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="The Mind Den",
        description="Backend API для Mind Den бота",
        version="0.1.0",
    )
    app.include_router(health_router)
    app.include_router(messages_router)
    app.include_router(reminders_router)
    app.include_router(skills_router)
    return app
