import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Whitelist: список разрешённых Telegram user_id
_raw_ids = os.getenv("ALLOWED_USER_IDS", "")
ALLOWED_USER_IDS: list[int] = [int(x.strip()) for x in _raw_ids.split(",") if x.strip().isdigit()]

# OpenRouter
OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-120b")
OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

# Groq
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

# Корень проекта дашборда (для code assistant)
PROJECT_ROOT: str = os.getenv("PROJECT_ROOT", "")

# SQLite — переопределяется через DB_PATH в .env (для Docker: /data/the_mind_den.db)
DB_PATH: str = os.getenv("DB_PATH", os.path.join(os.path.dirname(__file__), "data.db"))
