import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    COMFYUI_IMAGE_URL: str = os.getenv("COMFYUI_IMAGE_URL", "http://localhost:8188")
    COMFYUI_VIDEO_URL: str = os.getenv("COMFYUI_VIDEO_URL", "http://localhost:8288")
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")
    STORAGE_BASE: str = os.getenv("STORAGE_BASE", "/srv/lookbook")
    GUARD_SCRIPT: str = "/opt/lookbook/scripts/gpu-guard.sh"


settings = Settings()
