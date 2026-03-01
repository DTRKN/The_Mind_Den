import os
from dotenv import load_dotenv

load_dotenv()

# Telegram — поддержка обоих вариантов имени переменной
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN", "")

# Whitelist: список разрешённых Telegram user_id
# Поддержка ALLOWED_USER_IDS (список через запятую) и ALLOWED_USER_ID (один ID)
_raw_ids = os.getenv("ALLOWED_USER_IDS") or os.getenv("ALLOWED_USER_ID", "")
ALLOWED_USER_IDS: list[int] = [int(x.strip()) for x in _raw_ids.split(",") if x.strip().isdigit()]

# OpenRouter — поддержка MODEL и OPENROUTER_MODEL
OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL") or os.getenv("MODEL", "openai/gpt-4o-mini")
OPENROUTER_BASE_URL: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

# OpenAI (для embeddings text-embedding-3-small)
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

# Pinecone (векторная БД для memory_tool)
PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "the-mind-den-memory")

# Groq
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

# Файловый workspace (ограничение для file_tool)
WORKSPACE_DIR: str = os.getenv("WORKSPACE_DIR", "./workspace")

# Параметры агента
HISTORY_LIMIT: int = int(os.getenv("HISTORY_LIMIT", "20"))
VECTOR_SEARCH_LIMIT: int = int(os.getenv("VECTOR_SEARCH_LIMIT", "5"))

# Корень проекта дашборда (для code assistant)
PROJECT_ROOT: str = os.getenv("PROJECT_ROOT", "")

# SQLite — переопределяется через DB_PATH в .env (для Docker: /data/the_mind_den.db)
DB_PATH: str = os.getenv("DB_PATH", os.path.join(os.path.dirname(__file__), "data.db"))
