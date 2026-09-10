import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    app_name: str = "SSNS"
    environment: str = os.getenv("APP_ENV", "development")
    database_path: str = os.getenv("DATABASE_PATH", "./ssns.db")
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY") or None


settings = Settings()
