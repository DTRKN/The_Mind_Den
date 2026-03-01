# The Mind Den — Bot Documentation

> Личный AI-ассистент в Telegram для управления задачами, напоминаниями и работой с кодом проекта.

---

## Версии

### `v0.2.0-alpha` — *Time Awareness + Stability* `[01.03.2026]` ✅ CURRENT

**Что нового:**
- ✅ AI знает текущую дату и время (динамический системный промпт)
- ✅ Парсер напоминаний использует `RELATIVE_BASE=datetime.now()` — "через 5 минут" работает корректно
- ✅ Новая команда `/status` — время сервера, модель, режим, кол-во напоминаний
- ✅ Исправлен `AttributeError: Message.text` (иммутабельность в ptb v22)

---

### `v0.1.0-alpha` — *Python MVP* `[01.03.2026]` ✅ RELEASED

**Стек:** Python 3.14 · python-telegram-bot v22.6 · SQLite (aiosqlite) · APScheduler · OpenRouter · Groq Whisper

**Что реализовано:**
- ✅ Whitelist — доступ только по `ALLOWED_USER_IDS`
- ✅ AI-чат через OpenRouter с историей диалога (последние 12 сообщений)
- ✅ Смена модели на лету: `/model`, `/models`
- ✅ Напоминания из свободного текста — `dateparser` с поддержкой русского языка
- ✅ APScheduler — уведомления строго в заданное время
- ✅ Code Assistant режим — tool calling: `read_file`, `write_file`, `list_dir`, `git`
- ✅ Голос → текст через Groq Whisper (whisper-large-v3-turbo)
- ✅ SQLite: таблицы `reminders` и `chat_history`

**Исправленные баги:**
- ⚠️ Несовместимость `python-telegram-bot 21.3` с Python 3.14 → обновлено до v22.6
- ⚠️ `AttributeError: __stop_running_marker` → переход на `ApplicationBuilder` + `post_init`
- ⚠️ `AttributeError: Message.text can't be set` → рефакторинг в `_process_text()`

---

### `v0.3.0-beta` — *TypeScript Rewrite* `[запланировано]`

**Стек:** TypeScript · Grammy · Vercel AI SDK · Claude Sonnet · better-sqlite3 · node-cron · Zod

**Что планируется:**
- 🔲 Полная миграция на TypeScript (папка `ts-bot/`)
- 🔲 Grammy long polling
- 🔲 Vercel AI SDK `generateText` + `maxSteps: 5` (multi-turn tool calling)
- 🔲 Синхронный SQLite (better-sqlite3)
- 🔲 node-cron вместо APScheduler
- 🔲 Recurring напоминания (`cron_expr` в БД)
- 🔲 Memory Tool — поиск по истории сообщений

---

### `v0.4.0-beta` — *Vector Memory* `[запланировано]`

- 🔲 `sqlite-vec` — локальная векторная память без внешних сервисов
- 🔲 Семантический поиск по истории разговоров
- 🔲 "Что я просил сделать на прошлой неделе?" → релевантный ответ из истории

---

### `v1.0.0` — *Production* `[запланировано]`

- 🔲 Интеграция с ClickUp API — синхронизация задач
- 🔲 Интеграция с Google Calendar — события как напоминания
- 🔲 Управление Dashboard (Gravity Claw) через бота
- 🔲 Recurring напоминания с расписанием (ежедневно, еженедельно)

---

## Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Приветствие и полный список команд |
| `/help` | То же что `/start` |
| `/status` | Статус бота: время, модель, режим, напоминания |
| `/code` | Переключение в Code Assistant режим |
| `/chat` | Возврат в обычный AI-чат |
| `/model <name>` | Смена AI-модели (OpenRouter) |
| `/models` | Список популярных моделей |
| `/reminders` | Список активных напоминаний |
| `/cancel <id>` | Удалить напоминание по ID |
| `/clear` | Очистить историю чата |

---

## Как создать напоминание

Просто напиши в свободной форме:

```
напомни в 17:30 съесть морковь
напомни завтра в 9:00 позвонить маме
напомни через 2 часа сделать кофе
напомни сегодня в 20:00 о совещании
```

---

## Code Assistant режим

Команда `/code` переключает бота в режим работы с кодом. AI имеет доступ к файловой системе проекта (`PROJECT_ROOT` из `.env`).

**Примеры запросов:**
```
создай страницу Dashboard по пути gravity_claw/pages/Dashboard.tsx
покажи структуру проекта
прочитай файл Backend/config.py
сделай git commit с сообщением 'feat: add dashboard page'
```

**Доступные инструменты AI:**
| Инструмент | Описание |
|-----------|----------|
| `read_file` | Чтение файла из проекта |
| `write_file` | Создание / перезапись файла |
| `list_directory` | Список файлов и папок |
| `run_git_command` | Git: status, add, commit, log, diff |

---

## Структура проекта

```
The_Mind_Den/
├── Backend/                  ← Python бот (v0.1.x / v0.2.x)
│   ├── bot/
│   │   ├── ai_handler.py     ← OpenRouter чат + динамический промпт
│   │   ├── code_handler.py   ← Code Assistant (tool calling)
│   │   ├── handlers.py       ← Роутер команд + whitelist
│   │   ├── reminder_handler.py ← Управление напоминаниями
│   │   └── voice_handler.py  ← Groq Whisper транскрипция
│   ├── db/
│   │   └── database.py       ← SQLite CRUD (reminders, chat_history)
│   ├── scheduler/
│   │   └── scheduler.py      ← APScheduler (отправка уведомлений)
│   ├── utils/
│   │   └── parser.py         ← Парсинг дат из русского текста
│   ├── config.py             ← Чтение .env
│   ├── main.py               ← Точка входа
│   ├── data.db               ← SQLite БД (создаётся автоматически)
│   └── requirements.txt
│
├── gravity_claw/             ← Frontend Dashboard
├── .env                      ← Секреты (не в git!)
├── .env.example              ← Пример конфигурации
└── DOCS.md                   ← Этот файл
```

---

## Переменные окружения (`.env`)

```env
# Telegram
TELEGRAM_BOT_TOKEN=your_token_here

# Whitelist (Telegram user_id через запятую)
ALLOWED_USER_IDS=123456789

# OpenRouter
OPENROUTER_API_KEY=your_key_here
OPENROUTER_MODEL=openai/gpt-4o

# Groq (транскрипция голоса)
GROQ_API_KEY=your_key_here

# Корень проекта (для Code Assistant)
PROJECT_ROOT=c:\Users\doshi\Documents\Coding\The_Mind_Den
```

---

## Запуск

```powershell
cd C:\Users\doshi\Documents\Coding\The_Mind_Den\Backend
python main.py
```

---

## Changelog

### [0.2.0-alpha] — 01.03.2026
- Добавлены `_build_system_chat()` и `_build_system_code()` — динамический промпт с текущим временем
- Добавлен `RELATIVE_BASE=datetime.now()` в настройки dateparser
- Добавлена команда `/status`
- Рефакторинг `handle_text` → вынесена в `_process_text(update, context, text)` для поддержки голосовых сообщений
- `handle_reminder_text` принимает `text` как явный параметр

### [0.1.0-alpha] — 01.03.2026
- Первый запуск Python-бота
- Обновлена библиотека `python-telegram-bot` 21.3 → 22.6 (совместимость с Python 3.14)
- Исправлен `AttributeError: __stop_running_marker` — переход на `ApplicationBuilder` + `post_init`
- Исправлен `AttributeError: Message.text can't be set` (иммутабельность объектов в v22)
- Реализован whitelist через декоратор `@whitelist_only`
- Реализован Code Assistant с tool calling (read_file, write_file, list_dir, run_git_command)
- Реализован Groq Whisper для голосовых сообщений
- Реализован APScheduler для напоминаний с загрузкой pending задач при старте
