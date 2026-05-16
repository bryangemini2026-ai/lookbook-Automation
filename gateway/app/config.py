import os
from pydantic_settings import BaseSettings

# Resolve project root relative to this file
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_DEFAULT_DB = os.path.join(_PROJECT_ROOT, "data", "lookbook.db")


class Settings(BaseSettings):
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    SQLITE_PATH: str = _DEFAULT_DB
    COMFYUI_IMAGE_URL: str = "http://localhost:8188"
    COMFYUI_VIDEO_URL: str = "http://localhost:8288"
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
