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
- TASK-003 требует Node.js/npm для создания Vite проекта