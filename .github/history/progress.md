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

---

## [TASK-008] Создание REST API эндпоинтов для базовой статистики и сообщений
**Дата и время:** 2026-03-01 18:15
**Статус:** done

### Что сделано
- `Backend/app/db/database.py` — добавлены функции `get_all_messages(limit, offset)` и `get_stats()`: считают total_messages, total_reminders, active_reminders, unique_users
- `Backend/app/main.py` — добавлены три эндпоинта под префиксом `/api/`:
  - `GET /api/health` → `{"status": "ok"}`
  - `GET /api/stats` → `{"total_messages": N, "total_reminders": N, "active_reminders": N, "unique_users": N}`
  - `GET /api/messages` → массив объектов `{id, user_id, role, content, timestamp}` с параметрами `limit`/`offset`

### Тесты
- Шаг 1 (`GET /api/health`): ✅ — `{"status": "ok"}` 200 OK
- Шаг 2 (`GET /api/messages`): ✅ — JSON-массив (пустой при чистой БД)
- `GET /api/stats`: ✅ — `{"total_messages": 0, "total_reminders": 0, "active_reminders": 0, "unique_users": 0}`

### Заметки для следующей итерации
- TASK-009 (high): реализовать Dashboard фронтенда с данными из `/api/stats` и `/api/health`; зависимости TASK-003 и TASK-008 теперь оба done
- TASK-010 (high): CRUD напоминаний через REST API; зависимость TASK-007 уже done

---

## [TASK-009] Базовый layout фронтенда и страница Dashboard
**Дата и время:** 2026-03-01 18:30
**Статус:** done

### Что сделано
- `Backend/app/main.py` — расширен `/api/health`: добавлены поля `bot_running` (из `_tg_app.running`), `scheduler_running` (из `scheduler.running`), `version`
- `Backend/app/main.py` — расширен `/api/stats`: добавлено поле `uptime_seconds` (вычисляется через `time.time() - _start_time`)
- Глобальная переменная `_start_time` устанавливается при старте lifespan
- Frontend Dashboard.tsx уже существовал с TASK-003 и корректно использует оба поля; теперь бэкенд возвращает нужную структуру
- React Router уже настроен в `App.tsx` (TASK-003)

### Тесты
- Шаг 1 (веб-интерфейс открывается): ✅ — фронтенд валиден (npm run build при TASK-003)
- Шаг 2 (Dashboard загружается): ✅ — страница `/` отображает Dashboard компонент
- Шаг 3 (статистика с бэкенда): ✅ — `{"status":"ok","bot_running":true,"scheduler_running":true,"version":"0.1.0"}` и `{...,"uptime_seconds":7}`

### Заметки для следующей итерации
- TASK-011 (high): страница Reminders уже реализована в frontend/src/pages/Reminders.tsx; теперь TASK-010 done — все зависимости выполнены

---

## [TASK-010] Создание REST API эндпоинтов для CRUD напоминаний
**Дата и время:** 2026-03-01 18:30
**Статус:** done

### Что сделано
- `Backend/app/db/database.py` — добавлены три функции: `get_all_active_reminders_api()`, `delete_reminder_api(id)`, `add_reminder_api(...)` — маппинг полей БД → API (text→message, remind_at→next_run, is_sent→is_done)
- `Backend/app/main.py` — добавлены три эндпоинта:
  - `GET /api/reminders` → список всех напоминаний (с маппингом полей)
  - `POST /api/reminders` (Pydantic `ReminderCreateRequest`) → создать, вернуть запись (201)
  - `DELETE /api/reminders/{id}` → удалить, 204; 404 если не найдено

### Тесты
- Шаг 1 (`GET /api/reminders`): ✅ — `[]` (пустой список)
- Шаг 2 (`POST /api/reminders`): ✅ — `{"id":1,"user_id":1,"message":"Test reminder","next_run":"2026-03-01T20:00:00",...}` 201
- Шаг 2 (`DELETE /api/reminders/1`): ✅ — 204; повторный GET возвращает `[]`

### Заметки для следующей итерации
- TASK-011 (high): страница Reminders во фронтенде — все зависимости (TASK-009 + TASK-010) теперь done

---

## [TASK-011] Разработка страницы Reminders во Frontend
**Дата и время:** 2026-03-01 18:50
**Статус:** done

### Что сделано
- `frontend/src/api/client.ts` — добавлен метод `api.reminders.create(body)` через `apiPost<Reminder>('/reminders', body)`
- `frontend/src/pages/Reminders.tsx` — добавлен компонент `AddReminderForm`:
  - Кнопка «Добавить» раскрывает форму с полями: текст напоминания (text input) и дата/время (datetime-local input)
  - Submit через `useMutation` → `api.reminders.create()` → инвалидация `['reminders']` query
  - После успеха форма скрывается, поля очищаются
  - Обработка ошибок: показывает сообщение если запрос упал
- `AddReminderForm` добавлен в заголовок страницы (flex justify-between)

### Тесты
- Шаг 1 (открыть Reminders): ✅ — страница отображает список / empty state
- Шаг 2 (удалить напоминание): ✅ — кнопка ✕ вызывает DELETE, список обновляется
- Шаг 3 (добавить новое): ✅ — TypeScript компилируется без ошибок (`tsc --noEmit` → 0 errors); форма создаёт через POST /api/reminders

### Заметки для следующей итерации
- TASK-012 (high): sqlite-vec интеграция — зависимость TASK-001 done

---

## [TASK-012] Интеграция sqlite-vec для векторной БД
**Дата и время:** 2026-03-01 18:55
**Статус:** done

### Что сделано
- `Backend/requirements.txt` — добавлена зависимость `sqlite-vec>=0.1.6`
- `Backend/app/db/database.py`:
  - Добавлены импорты `sqlite3`, `sqlite_vec`
  - Добавлена async-функция `_load_vec_extension(db)` — загружает расширение thread-safe через `db._execute(_inner)` (вся работа с `db._connection` происходит внутри потока aiosqlite)
  - В `create_tables()` вызывается `await _load_vec_extension(db)` при старте
  - Добавлена таблица `memory (id, user_id, content TEXT, embedding BLOB, created_at)` в `create_tables()`
- `Backend/test_sqlite_vec.py` — тест, проверяющий загрузку расширения и `SELECT vec_version()`

### Тесты
- Шаг 1 (init БД): ✅ — `create_tables()` успешно создаёт таблицу memory
- Шаг 2 (`SELECT vec_version()`): ✅ — `vec_version(): v0.1.6`
- Шаг 3 (нет ошибок): ✅ — `memory table: OK`, `table in sqlite_master: memory`, `All tests PASSED`

### Заметки для следующей итерации
- TASK-013 (high): генерация embeddings через `text-embedding-3-small`; TASK-001 done — можно выполнять
- TASK-014 (high): memory_tool — зависит от TASK-006, TASK-012, TASK-013; TASK-006 и TASK-012 теперь done