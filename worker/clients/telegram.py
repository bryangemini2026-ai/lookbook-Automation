import os

import httpx

from config import settings


class TelegramNotifier:
    """Simple Telegram Bot API client for notifications."""

    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.token}"

    def send_message(self, text: str):
        """Send a text message."""
        if not self.token or not self.chat_id:
            return
        try:
            httpx.post(f"{self.base_url}/sendMessage", json={
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": "Markdown",
            }, timeout=10)
        except Exception as e:
            print(f"Telegram error: {e}")

    def send_photo(self, photo_bytes: bytes, caption: str = ""):
        """Send a photo with optional caption."""
        if not self.token or not self.chat_id:
            return
        try:
            httpx.post(f"{self.base_url}/sendPhoto", data={
                "chat_id": self.chat_id,
                "caption": caption,
            }, files={
                "photo": ("result.png", photo_bytes, "image/png"),
            }, timeout=30)
        except Exception as e:
            print(f"Telegram error: {e}")

    def notify_completion(self, job_id: str, results: dict):
        """Send job completion notification."""
        images = results.get("raw_images", [])
        count = len(images)
        msg = f"Job `{job_id[:8]}` completed!\n{count} images generated."

        if images and os.path.exists(images[0]):
            with open(images[0], "rb") as f:
                self.send_photo(f.read(), msg)
        else:
            self.send_message(msg)

    def notify_error(self, job_id: str, error: str):
        """Send error notification."""
        self.send_message(f"Job `{job_id[:8]}` FAILED:\n```\n{error[:500]}\n```")
