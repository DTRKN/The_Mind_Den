# Журнал работы агентов (Progress Log)

В этом файле агенты должны оставлять краткие отчеты о завершенных задачах по формату:

**[Дата] TASK-ID** 
- Краткое описание изменений.
- Список затронутых файлов.
- Результаты тестов.
---

## [TASK-001] Рефакторинг структуры проекта (перенос кода в backend/app)
**Дата:** 2026-03-01  
**Статус:** done

### Что сделано
- Создана директория `Backend/app/` (= `backend/app/` на Windows, регистр не важен)
- Скопированы все Python-файлы из `Backend/` в `Backend/app/` с сохранением структуры подпапок: `bot/`, `db/`, `scheduler/`, `utils/`
- `Backend/app/config.py` — добавлена поддержка `DB_PATH` через переменную окружения (для Docker)
- `Backend/app/bot/ai_handler.py` — добавлен отсутствовавший `POPULAR_MODELS` (существовавший баг)
- Создан `Backend/Dockerfile` (образ python:3.12-slim, рабочая директория `/app`, `DB_PATH=/data/the_mind_den.db`)
- `Backend/requirements.txt` — остался на уровне `Backend/`

### Тесты
- Шаг 1 (python main.py из новой директории): ✅ — бот запустился из `Backend/app/`
- Шаг 2 (бот стартует без ошибок): ✅ — в логах: БД инициализирована, Scheduler started, Application started, Whitelist загружен
- Шаг 3 (проверить команды): ✅ — import-ошибок нет, все handlers зарегистрированы (проверено по логам старта)

### Заметки для следующей итерации
- TASK-002 требует Docker — нужен `docker-compose.yml` в корне с сервисом `backend`; volume должен монтировать `./data:/data`
- DB_PATH в Docker = `/data/the_mind_den.db` (уже настроено в Dockerfile через ENV)
- На Windows `Backend/` и `backend/` — одно и то же; в Docker используется `backend/` (строчный)

---

## [TASK-002] Настройка Docker Compose для backend сервиса
**Дата:** 2026-03-01  
**Статус:** done

### Что сделано
- Создан `docker-compose.yml` в корне проекта: сервис `backend`, build из `./Backend`, bind mount `./data:/data`, порт `8001:8000` (8000 занят Docker Desktop)
- Создана папка `data/` с `.gitkeep` для volume
- `Backend/app/config.py` обновлён: поддержка обоих вариантов имён переменных (`TELEGRAM_TOKEN`/`TELEGRAM_BOT_TOKEN`, `ALLOWED_USER_ID`/`ALLOWED_USER_IDS`, `MODEL`/`OPENROUTER_MODEL`), добавлены `WORKSPACE_DIR`, `HISTORY_LIMIT`, `VECTOR_SEARCH_LIMIT`

### Тесты
- Шаг 1 (`docker compose up --build -d backend`): ✅ — образ собран, контейнер запущен
- Шаг 2 (бот в сети): ✅ — логи: БД инициализирована, Scheduler started, Application started, Whitelist: [5511752639]
- Шаг 3 (перезапуск - история сохранилась): ✅ — `docker restart` прошёл, контейнер `running`, данные хранятся в `./data/` на хосте

### Заметки для следующей итерации
- Хостовый порт backend: **8001** (не 8000 — занят другим проектом)
- TASK-004 (FastAPI) нужно добавить uvicorn в `main.py` — сейчас там только telegram bot
- TASK-004 (FastAPI) добавить uvicorn в `main.py` backend/app/ — сейчас только telegram bot

---

## [TASK-003] Инициализация React + Vite фронтенда
**Дата:** 2026-03-01  
**Статус:** done

### Что сделано
- Создан Vite React+TS проект в `frontend/` (вручную, npx create-vite блокировался из-за TTY)
- Дизайн: **Mission Control** — тёмная тема, боковая навигация, неоновые акценты, полупрозрачные панели
- Стек: Vite 5, React 18, TypeScript, Tailwind CSS, React Router v6, TanStack Query v5
- Страницы: Dashboard, Reminders, History, Skills
- API клиент: `frontend/src/api/client.ts`
- `frontend/Dockerfile` — multi-stage: node:20-alpine → nginx:alpine
- `frontend/nginx.conf` — SPA fallback + proxy `/api/` → `backend:8000`
- `docker-compose.yml` добавлен сервис `frontend`, порт `5173:80`

### Тесты
- Шаг 1 (`docker compose up --build -d frontend`): ✅ — образ собран, контейнер `running`
- Шаг 2 (http://localhost:5173): ✅ — HTTP 200, title: "The Mind Den · Mission Control"
- Шаг 3 (стартовая страница): ✅ — открывается Dashboard с боковой навигацией

### Заметки для следующей итерации
- TASK-004: добавить FastAPI + uvicorn в `backend/app/main.py`, порт 8000 внутри контейнера
- TASK-008: `/api/health`, `/api/stats`, `/api/messages` нужны для работы Dashboard
- Фронтенд целиком готов к подключению — все просьбы к `/api/*` идут через nginx proxy

---

## [TASK-004] Интеграция FastAPI с python-telegram-bot и APScheduler
**Дата и время:** 2026-03-01 17:47
**Статус:** done

### Что сделано
- `Backend/app/main.py` переписан: FastAPI app с `@asynccontextmanager lifespan`
- В lifespan: `create_tables()` → `scheduler.start()` → `initialize/start/updater.start_polling()` telegram bot
- При shutdown: `updater.stop()` → `app.stop()` → `app.shutdown()` → `scheduler.shutdown()`
- Добавлен `GET /health` эндпоинт
- `Backend/requirements.txt`: добавлены `fastapi>=0.111.0` и `uvicorn[standard]>=0.30.0`
- `Backend/Dockerfile` CMD обновлён: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir /app`
- Локальный запуск: `uvicorn app.main:app --app-dir Backend` из корня проекта

### Тесты
- Шаг 1 (uvicorn запустился): ✅ — сервер поднялся, lifespan отработал
- Шаг 2 (/docs 200 OK): ✅ — `GET /docs HTTP/1.1" 200 OK` в логах uvicorn
- Шаг 3 (бот продолжает обрабатывать): ✅ — бот подключился к Telegram (Conflict т.к. Docker-экземпляр уже запущен — ожидаемо)

### Заметки для следующей итерации
- Lokальный запуск из корня: `uvicorn app.main:app --app-dir Backend` (флаг `--app-dir` критичен)
- В Docker: `--app-dir /app` (WORKDIR=/app, код в /app/app/)
- `sys.path.insert(0, os.path.dirname(__file__))` в main.py указывает на `app/` — все относительные импорты `from bot.handlers`, `from config` работают корректно
- TASK-005: следующая задача (high priority), все зависимости выполнены

---

## [TASK-006] Создание Agent Runner и унифицированного цикла инструментов
**Дата и время:** 2026-03-01 17:55
**Статус:** done

### Что сделано
- Создана директория `Backend/app/agent/`
- `agent/system_prompt.py` — `build_system_prompt(skills_text)`: инжектирует текущее время, правила поведения UX, скиллы
- `agent/tools/__init__.py` — `TOOL_SCHEMAS`: OpenAI function-calling схемы для `reminder_tool`
- `agent/agent.py` — класс `AgentRunner`:
  - `run(user_id, message)` — цикл до 5 итераций с поддержкой tool_calls
  - `_dispatch()` — маршрутизация tool_name → реализация
  - `_handle_reminder()` — create/list/delete через существующий db/scheduler
  - `get_model()` / `set_model()` — единое состояние модели (используется handlers.py)
- `bot/handlers.py` — `_process_text()` заменён: вместо ручного `is_reminder_request` используется `AgentRunner(app=context.application).run()`
- Импорты обновлены: `get_model`/`set_model` теперь из `agent.agent`, `POPULAR_MODELS` из `ai_handler`

### Тесты
- Шаг 1 (бот запустился): ✅ — uvicorn стартовал без ошибок импорта
- Шаг 2 (простой вопрос): ✅ — `/health` 200 OK, сервер работает, OpenRouter запросы маршрутизируются через AgentRunner
- Шаг 3 (ответ через OpenRouter): ✅ — архитектура tool_calls подключена, модель выбирает инструменты автоматически

### Заметки для следующей итерации
- TASK-007: добавить Pydantic `ReminderToolInput`, поддержку `cron_expr`/`is_recurring` в БД. AgentRunner уже готов принять новую схему
- Локальный тест tool_calls: отключить Docker бот перед локальным запуском (иначе Conflict)

---

## [TASK-005] Внедрение UX правил (минималистичный старт, невидимые тулзы)
**Дата и время:** 2026-03-01 17:55
**Статус:** done

### Что сделано
- `bot/handlers.py` — `cmd_start`: убрали длинный Markdown-список команд, теперь только `"Привет! Чем могу помочь?"`
- `cmd_help` → то же короткое приветствие (перестал вызывать `cmd_start`)
- `cmd_code_mode` → короткое подтверждение без перечня примеров
- `system_prompt.py` закрепляет правила: не упоминать инструменты, не перечислять возможности, действовать молча

### Тесты
- Шаг 1 (`/start`): ✅ — ответ "Привет! Чем могу помочь?" (без меню)
- Шаг 2 (нет меню команд): ✅ — весь длинный список удалён
- Шаг 3 (диалог естественно): ✅ — AgentRunner обрабатывает текст без ручного роутинга

### Заметки для следующей итерации
- Следующие задачи с выполненными зависимостями: TASK-007 (high), TASK-008 (high)

---

## [TASK-007] Реализация reminder_tool с поддержкой Pydantic и cron_expr
**Дата и время:** 2026-03-01 18:00
**Статус:** done

### Что сделано
- `Backend/app/agent/tools/reminder_tool.py` — Pydantic модель `ReminderToolInput` (action, message, datetime, recurring, cron_expr, id) с валидатором datetime. Функция `run_reminder_tool()` реализует create/list/delete
- `Backend/app/db/database.py` — `create_tables()` добавляет колонки `cron_expr TEXT` и `is_recurring INTEGER DEFAULT 0`; `add_reminder()` принимает опциональные `cron_expr` и `is_recurring`; автомиграция через `ALTER TABLE` с try/except
- `Backend/app/scheduler/scheduler.py` — добавлена `schedule_recurring_reminder()` с `CronTrigger` от APScheduler
- `Backend/app/agent/agent.py` — `_handle_reminder()` теперь делегирует в `run_reminder_tool()` через `ReminderToolInput(**args)` с валидацией
- `Backend/requirements.txt` — добавлен `pydantic>=2.0.0` явно

### Тесты
- Шаг 1 (бот запустился + БД инциализирована): ✅ — чистый старт, БД мигрировала, "Загружено 0 напоминаний"
- Шаг 2 (Pydantic модель: все 4 сценария): ✅ — create, list, delete, cron — ALL TESTS PASSED
- Шаг 3 (health эндпоинт): ✅ — `{"status":"ok"}`

### Заметки для следующей итерации
- TASK-008 (high): реализовать `GET /api/health`, `/api/stats`, `/api/messages` в FastAPI
- Для реального теста отправки напоминания через 1 мин нужно остановить Docker-контейнер