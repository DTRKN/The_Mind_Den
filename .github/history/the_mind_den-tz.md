# Техническое Задание: The Mind Den

**Версия:** 2.0  
**Дата:** 2026-03-01  
**Статус:** Draft

---

## 1. Обзор проекта

**The Mind Den** — персональный AI-ассистент, работающий локально и доступный через Telegram. Ассистент способен отвечать на вопросы, искать информацию в интернете, создавать напоминания, работать с файлами, анализировать данные и расширять свои возможности через систему скиллов.

Ассистент работает в режиме **long polling** (без вебхуков), полностью локально на машине пользователя.

**Архитектура:** Python backend + React frontend, всё завёрнуто в Docker.

---

## 2. Цели и ценность

| Цель | Описание |
|------|----------|
| Единая точка входа | Всё через Telegram — привычный интерфейс, без дополнительных приложений |
| Умный ассистент | Понимает намерение пользователя и выбирает нужный инструмент сам |
| Расширяемость | Новые скиллы добавляются без изменения ядра |
| Локальность | Нет зависимости от внешних серверов, данные хранятся локально |

---

## 3. Функциональные требования

### 3.1 Базовый чат
- Ассистент принимает текстовые сообщения от пользователя в Telegram
- Сохраняет историю диалога в SQLite
- Отвечает с учётом контекста последних сообщений
- Показывает индикатор "печатает..." во время генерации ответа

### 3.2 Напоминания
- Пользователь говорит в свободной форме: "напомни мне завтра в 9 сходить в магазин"
- Агент разбирает намерение и вызывает `reminder_tool`
- Поддержка разовых и повторяющихся напоминаний (cron-формат)
- Напоминание приходит в Telegram в нужное время
- Управление: показать список, удалить, изменить

### 3.3 Веб-поиск и анализ
- При вопросах, требующих актуальных данных, агент самостоятельно инициирует поиск
- Поиск через Tavily API или Brave Search API
- Результаты обрабатываются агентом и возвращаются в виде структурированного ответа
- При анализе — агент может делать несколько поисковых запросов и синтезировать ответ

### 3.4 Работа с файлами
- Чтение текстовых файлов по указанному пути
- Запись/создание файлов
- Поиск по содержимому файлов в указанной директории
- Ограничение: только пути внутри разрешённой `WORKSPACE_DIR`

### 3.5 Память (контекстная)
- Краткосрочная: последние N сообщений из SQLite (скользящее окно)
- Долгосрочная: векторное хранилище (sqlite-vec) — смысловой поиск по всей истории
- При каждом запросе агент получает: `[релевантный контекст из прошлого]` + `[последние сообщения]`
- Пользователь может явно сохранить что-то: "запомни, что я предпочитаю краткие ответы"

### 3.6 Скиллы
- Скилл — папка с `SKILL.md` файлом (название, описание, инструкции)
- Скиллы хранятся в `skills/` директории проекта
- При старте агента все скиллы загружаются в system prompt
- Агент знает, когда и как применять каждый скилл
- Поддержка **self-extending**: агент может создать новый скилл по запросу пользователя ("добавь скилл для работы с SQLite")
- Скиллы могут содержать: инструкции, скрипты, референсы

---

## 4. Нефункциональные требования

| Параметр | Требование |
|----------|-----------|
| Платформа | Docker (локально), Windows/macOS/Linux через Docker Desktop |
| Транспорт | Telegram Bot API, long polling (без вебхука) |
| Хранилище | SQLite (volume внутри Docker) |
| Backend | Python ≥ 3.12 |
| Frontend | React + TypeScript (Vite) |
| Запуск | `docker compose up` |
| Конфиг | `.env` файл |
| Доступ | Только whitelist `userId` из `.env` (один пользователь) |

---

## 5. Технический стек

### Backend (Python)
```
python-telegram-bot       — Telegram Bot (polling)
openai                    — OpenRouter API (OpenAI-совместимый клиент)
aiosqlite                 — асинхронный SQLite
sqlite-vec                — векторное расширение для SQLite
apscheduler               — планировщик cron-задач
fastapi                   — REST API для фронтенда
uvicorn                   — ASGI сервер
pydantic                  — валидация данных
python-dotenv             — переменные окружения
httpx                     — HTTP-клиент для веб-поиска
```

> **OpenRouter** предоставляет OpenAI-совместимый API с доступом к сотням моделей.
> Используется стандартный `openai` Python SDK с заменой `base_url` на `https://openrouter.ai/api/v1`.

### Frontend (React)
```
react + vite              — основа фронтенда
typescript                — типизация
tailwindcss               — стили
tanstack-query            — запросы к backend API
react-router-dom          — роутинг
```

### Инфраструктура
```
docker + docker compose   — контейнеризация
nginx (опционально)       — проксирование frontend → backend
```

---

## 6. Архитектура

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Compose                        │
│                                                          │
│  ┌─────────────┐        ┌──────────────────────────┐    │
│  │  frontend   │◄──────►│       backend            │    │
│  │  React/Vite │  REST  │       FastAPI             │    │
│  │  :5173      │  API   │       :8000               │    │
│  └─────────────┘        │                          │    │
│                          │  ┌─────────────────────┐ │    │
│                          │  │  Telegram Bot        │ │    │
│                          │  │  (long polling)      │ │    │
│                          │  └────────┬────────────┘ │    │
│                          │           │               │    │
│                          │  ┌────────▼────────────┐ │    │
│                          │  │  Agent Runner        │ │    │
│                          │  │  system prompt       │ │    │
│                          │  │  + skills injection  │ │    │
│                          │  │  + tools             │ │    │
│                          │  └────────┬────────────┘ │    │
│                          │           │ OpenRouter API│    │
│                          │  ┌────────▼────────────┐ │    │
│                          │  │  Tools               │ │    │
│                          │  │  reminder / memory   │ │    │
│                          │  │  web_search / file   │ │    │
│                          │  │  skill_tool          │ │    │
│                          │  └────────┬────────────┘ │    │
│                          │           │               │    │
│                          │  ┌────────▼────────────┐ │    │
│                          │  │  SQLite + sqlite-vec  │ │    │
│                          │  │  /data/the_mind_den.db│ │    │
│                          │  └─────────────────────┘ │    │
│                          │                          │    │
│                          │  APScheduler             │    │
│                          │  (cron worker)           │    │
│                          └──────────────────────────┘    │
│                                    │                      │
│                            volume: ./data                 │
└─────────────────────────────────────────────────────────┘
                                     │
                              Telegram API
```

---

## 7. Структура файлов

```
the_mind_den/
├── backend/                          ← Python сервис
│   ├── app/
│   │   ├── main.py                   ← точка входа: FastAPI + bot + cron
│   │   │
│   │   ├── bot/
│   │   │   └── handlers.py           ← python-telegram-bot handlers
│   │   │
│   │   ├── agent/
│   │   │   ├── agent.py              ← OpenRouter + tools loop
│   │   │   ├── system_prompt.py      ← промпт + инъекция скиллов
│   │   │   └── tools/
│   │   │       ├── reminder_tool.py  ← создать/список/удалить напоминание
│   │   │       ├── memory_tool.py    ← сохранить/найти (векторный поиск)
│   │   │       ├── web_search_tool.py← поиск через Tavily API
│   │   │       ├── file_tool.py      ← чтение/запись файлов
│   │   │       └── skill_tool.py     ← создать новый скилл
│   │   │
│   │   ├── db/
│   │   │   ├── init.py               ← инит SQLite + таблицы
│   │   │   ├── messages.py           ← get_history(), save_message()
│   │   │   ├── reminders.py          ← CRUD напоминаний
│   │   │   └── vectors.py            ← embeddings + semantic search
│   │   │
│   │   ├── cron/
│   │   │   └── worker.py             ← APScheduler: getDue() → sendMessage()
│   │   │
│   │   ├── skills/
│   │   │   └── loader.py             ← читает SKILL.md → system prompt
│   │   │
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── reminders.py      ← GET/POST/DELETE /api/reminders
│   │   │   │   ├── messages.py       ← GET /api/messages (история)
│   │   │   │   ├── skills.py         ← GET/POST /api/skills
│   │   │   │   └── stats.py          ← GET /api/stats
│   │   │   └── router.py             ← регистрация роутов
│   │   │
│   │   └── config.py                 ← настройки через pydantic-settings
│   │
│   ├── skills/                       ← SKILL.md файлы
│   │   ├── web-research/
│   │   │   └── SKILL.md
│   │   └── file-manager/
│   │       └── SKILL.md
│   │
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/                         ← React приложение
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx         ← главная: статус бота, статистика
│   │   │   ├── Reminders.tsx         ← список/создание/удаление напоминаний
│   │   │   ├── History.tsx           ← история диалогов
│   │   │   └── Skills.tsx            ← список скиллов, добавление
│   │   ├── components/
│   │   │   ├── ReminderCard.tsx
│   │   │   ├── MessageBubble.tsx
│   │   │   └── SkillCard.tsx
│   │   └── api/
│   │       └── client.ts             ← axios/fetch к backend :8000
│   ├── Dockerfile
│   ├── package.json
│   └── vite.config.ts
│
├── data/                             ← Docker volume
│   └── the_mind_den.db               ← SQLite (auto-created)
│
├── docker-compose.yml
├── .env
└── README.md
```

---

## 8. Схема базы данных

```sql
-- История сообщений
CREATE TABLE messages (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id    TEXT        NOT NULL,
  role       TEXT        NOT NULL,   -- 'user' | 'assistant'
  content    TEXT        NOT NULL,
  created_at DATETIME    DEFAULT CURRENT_TIMESTAMP
);

-- Векторная память
CREATE TABLE memory (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id    TEXT        NOT NULL,
  content    TEXT        NOT NULL,   -- исходный текст
  embedding  BLOB        NOT NULL,   -- float32 вектор
  source     TEXT,                   -- 'user_explicit' | 'auto'
  created_at DATETIME    DEFAULT CURRENT_TIMESTAMP
);

-- Напоминания
CREATE TABLE reminders (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id      TEXT     NOT NULL,
  message      TEXT     NOT NULL,
  cron_expr    TEXT,                 -- NULL = разовое
  next_run     DATETIME NOT NULL,
  is_recurring INTEGER  DEFAULT 0,
  is_done      INTEGER  DEFAULT 0,
  created_at   DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 9. Tools — спецификация (Python)

### reminder_tool
```python
class ReminderToolInput(BaseModel):
    action: Literal['create', 'list', 'delete']
    message: Optional[str] = None       # текст напоминания
    datetime: Optional[str] = None      # ISO 8601
    recurring: Optional[bool] = False
    cron_expr: Optional[str] = None     # '0 8 * * *'
    id: Optional[int] = None            # для delete

# output: { "success": bool, "data": any }
```

### memory_tool
```python
class MemoryToolInput(BaseModel):
    action: Literal['save', 'search']
    content: Optional[str] = None       # что сохранить
    query: Optional[str] = None         # что искать
    limit: Optional[int] = 5

# output: { "results": list[str], "success": bool }
```

### web_search_tool
```python
class WebSearchToolInput(BaseModel):
    query: str
    limit: Optional[int] = 5

# output: { "results": [{"title", "url", "snippet"}] }
```

### file_tool
```python
class FileToolInput(BaseModel):
    action: Literal['read', 'write', 'list']
    path: str                           # относительно WORKSPACE_DIR
    content: Optional[str] = None       # для write

# output: { "content": str, "files": list[str], "success": bool }
```

### skill_tool
```python
class SkillToolInput(BaseModel):
    action: Literal['create', 'list']
    name: Optional[str] = None
    description: Optional[str] = None
    instructions: Optional[str] = None

# output: { "success": bool, "path": str }
```

---

## 10. Формат скилла (SKILL.md)

```markdown
---
name: web-research
description: Глубокий веб-поиск и анализ информации. Использовать когда нужны актуальные данные, новости, факты.
---

# Web Research

## Когда применять
- Вопросы о текущих событиях
- Поиск технической документации
- Анализ темы по нескольким источникам

## Процесс
1. Сформулировать 2-3 поисковых запроса
2. Запустить web_search_tool для каждого
3. Синтезировать результаты в связный ответ
4. Указать источники

## Правила
- Всегда указывать источники
- Отмечать если информация устарела
```

---

## 11. Поведение бота (UX-правила)

### Правило 1 — Никакого перечисления возможностей
- При `/start` и любом первом сообщении бот **не пишет** список команд, инструментов и функций
- Бот отвечает естественно на то, что написал пользователь
- Все инструменты работают **под капотом** — пользователь их не видит

**Плохо (запрещено):**
```
Привет! Я The Mind Den. Вот что я умею:
• 📅 Напоминания — /reminder
• 🔍 Поиск — /search
• 📁 Файлы — /file
• ...
```

**Хорошо:**
```
Пользователь: /start
The Mind Den: Привет! Чем могу помочь?

Пользователь: Напомни мне завтра в 9 утра про встречу
The Mind Den: Готово, напомню завтра в 09:00 про встречу.
```

### Правило 2 — Агент выводит из сообщения, не спрашивает лишнего
- Если пользователь написал достаточно — агент действует сразу
- Уточняет только если информации критически не хватает (например, не указано время)
- Не задаёт несколько вопросов подряд

### Правило 3 — Инструменты вызываются молча
- Пользователь не видит `tool_call`, `function_call`, названия инструментов
- Агент пишет результат в человекочитаемом виде
- Если инструмент отработал — бот пишет итог, не описывая процесс

### Правило 4 — Обработка `/start`
```python
# handlers.py
async def start_command(update, context):
    await update.message.reply_text("Привет! Чем могу помочь?")
    # Никакого Markdown с списком команд
```

---

## 12. System Prompt (структура)

```
Ты — The Mind Den, персональный AI-ассистент.

Правила поведения:
- Отвечай естественно, как умный помощник
- Никогда не упоминай названия инструментов в ответах пользователю
- Не перечисляй свои возможности, если тебя об этом не спросили
- Действуй на основе сообщения пользователя — выводи намерение и выполняй
- Если нужен поиск — ищи молча, дай результат
- Если нужно напоминание — создай молча, подтверди коротко

## Активные скиллы
[динамически инжектируется из skills/*.SKILL.md]

## Текущее время
[инжектируется при каждом запросе]
```

---

## 12. Конфигурация

### .env (корень проекта)
```env
# Telegram
TELEGRAM_TOKEN=your_bot_token
ALLOWED_USER_ID=123456789

# AI — OpenRouter
OPENROUTER_API_KEY=sk-or-...
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
# Модель: любая доступная на openrouter.ai (например anthropic/claude-3.5-sonnet, openai/gpt-4o и др.)
MODEL=anthropic/claude-3.5-sonnet

# Поиск
SEARCH_API_KEY=tvly-...          # Tavily API key

# Файлы
WORKSPACE_DIR=./workspace

# Параметры агента
HISTORY_LIMIT=20
VECTOR_SEARCH_LIMIT=5

# Backend
BACKEND_PORT=8000

# Frontend
FRONTEND_PORT=5173
VITE_API_URL=http://localhost:8000
```

### docker-compose.yml
```yaml
version: '3.9'

services:
  backend:
    build: ./backend
    ports:
      - "${BACKEND_PORT:-8000}:8000"
    volumes:
      - ./data:/app/data
      - ./backend/skills:/app/skills
    env_file: .env
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports:
      - "${FRONTEND_PORT:-5173}:80"
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  data:
```

### backend/Dockerfile
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Код
COPY app/ ./app/
COPY skills/ ./skills/

# База данных
RUN mkdir -p /app/data

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### frontend/Dockerfile
```dockerfile
FROM node:22-alpine AS builder

WORKDIR /app
COPY package*.json .
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
```

---

## 13. Этапы разработки (MVP → Full)

### Этап 1 — Backend основа (≈ 3 часа)
- [ ] Инициализация Python проекта + `requirements.txt`
- [ ] `python-telegram-bot` polling + echo-ответ
- [ ] SQLite инит + таблицы (`aiosqlite`)
- [ ] Базовый агент (Claude без tools, история в контексте)
- [ ] Docker + docker-compose запуск

**Результат:** `docker compose up` → бот отвечает через Claude

### Этап 2 — FastAPI + Frontend основа (≈ 3 часа)
- [ ] FastAPI сервер с базовыми роутами
- [ ] React + Vite проект
- [ ] Dashboard страница (статус бота)
- [ ] History страница (история диалогов)
- [ ] Docker для frontend (nginx)

**Результат:** Веб-интерфейс показывает историю разговоров

### Этап 3 — Напоминания (≈ 2.5 часа)
- [ ] `reminder_tool` (create/list/delete)
- [ ] APScheduler worker
- [ ] API роут `/api/reminders`
- [ ] Frontend страница Reminders

**Результат:** "Напомни мне завтра в 9" → уведомление в Telegram + видно в UI

### Этап 4 — Память (≈ 3 часа)
- [ ] sqlite-vec подключение
- [ ] Embeddings через OpenAI `text-embedding-3-small`
- [ ] `memory_tool` (save/search)
- [ ] Авто-сохранение важных фактов

**Результат:** Агент помнит из прошлых разговоров

### Этап 5 — Веб-поиск (≈ 1.5 часа)
- [ ] Tavily API клиент
- [ ] `web_search_tool`
- [ ] Скилл `web-research/SKILL.md`

**Результат:** "Что нового в AI?" → поиск → ответ

### Этап 6 — Скиллы и файлы (≈ 3 часа)
- [ ] `skill_tool` (create/list)
- [ ] `file_tool` (read/write/list)
- [ ] Загрузчик скиллов
- [ ] Frontend страница Skills

**Результат:** Агент пишет новые скиллы, работает с файлами

---

## 14. Критерии готовности MVP

- [ ] Запуск одной командой: `docker compose up`
- [ ] Бот отвечает только авторизованному пользователю (`ALLOWED_USER_ID`)
- [ ] Помнит контекст разговора (SQLite история)
- [ ] Создаёт напоминания и отправляет их в нужное время
- [ ] Ищет информацию в интернете по запросу
- [ ] Загружает и применяет скиллы при старте
- [ ] При перезапуске и пересборке Docker данные сохраняются (volume)
- [ ] Фронтенд доступен на `localhost:5173` и показывает историю
- [ ] Фронтенд позволяет управлять напоминаниями без Telegram

---

## 15. API эндпоинты (Backend → Frontend)

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/messages` | История сообщений |
| GET | `/api/reminders` | Список напоминаний |
| POST | `/api/reminders` | Создать напоминание |
| DELETE | `/api/reminders/{id}` | Удалить напоминание |
| GET | `/api/skills` | Список скиллов |
| POST | `/api/skills` | Создать скилл |
| GET | `/api/stats` | Статистика (токены, кол-во сообщений) |
| GET | `/api/health` | Статус бота |
