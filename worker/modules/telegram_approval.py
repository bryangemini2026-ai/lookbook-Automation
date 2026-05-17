"""
Telegram Approval System with inline buttons.

Each pipeline step sends results to Telegram and waits for approval.
Buttons: ✅ 통과 / 🔄 재생성 / ✏️ 수정요청

Usage:
    approval = TelegramApproval()
    result = await approval.request_approval(
        step="image_gen",
        images=[image_bytes],
        caption="이미지 생성 완료. 승인해주세요."
    )
    # result = "approve" | "retry" | "edit:수정내용"
"""

import json
import time
import os
import threading
from datetime import datetime
from enum import Enum

import httpx

from config import settings


class ApprovalResult(str, Enum):
    APPROVE = "approve"
    RETRY = "retry"
    EDIT = "edit"


class TelegramApproval:
    """
    Sends results to Telegram with inline approval buttons.
    Waits for user response via polling.
    """

    BASE_URL = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"

    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self._pending: dict[str, dict] = {}  # callback_id -> {result, edit_text}
        self._offset = 0
        self._polling = False
        self._poll_thread = None

    def _start_polling(self):
        """Start polling for callback queries in background thread."""
        if self._polling:
            return
        self._polling = True
        self._poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._poll_thread.start()

    def _poll_loop(self):
        """Poll Telegram for callback queries."""
        while self._polling:
            try:
                resp = httpx.get(f"{self.BASE_URL}/getUpdates", params={
                    "offset": self._offset,
                    "timeout": 5,
                    "allowed_updates": '["callback_query"]',
                }, timeout=10)
                data = resp.json()

                for update in data.get("result", []):
                    self._offset = update["update_id"] + 1
                    callback = update.get("callback_query")
                    if callback:
                        self._handle_callback(callback)

            except Exception as e:
                print(f"[ApprovalPoll] Error: {e}")
            time.sleep(1)

    def _handle_callback(self, callback: dict):
        """Handle inline button callback."""
        callback_id = callback["id"]
        data = callback.get("data", "")
        message_id = callback["message"]["message_id"]

        # Parse callback data: "approve:JOB_ID" or "retry:JOB_ID" or "edit:JOB_ID"
        parts = data.split(":", 1)
        action = parts[0]
        job_id = parts[1] if len(parts) > 1 else ""

        if job_id in self._pending:
            if action == "approve":
                self._pending[job_id]["result"] = ApprovalResult.APPROVE
            elif action == "retry":
                self._pending[job_id]["result"] = ApprovalResult.RETRY
            elif action == "edit":
                self._pending[job_id]["result"] = ApprovalResult.EDIT

        # Answer callback query to remove loading indicator
        try:
            httpx.post(f"{self.BASE_URL}/answerCallbackQuery", json={
                "callback_query_id": callback_id,
                "text": self._get_confirm_text(action),
            }, timeout=5)
        except Exception:
            pass

        # Update message to show selection
        try:
            httpx.post(f"{self.BASE_URL}/editMessageReplyMarkup", json={
                "chat_id": self.chat_id,
                "message_id": message_id,
                "reply_markup": json.dumps({"inline_keyboard": []}),
            }, timeout=5)
        except Exception:
            pass

    def _get_confirm_text(self, action: str) -> str:
        texts = {
            "approve": "✅ 승인되었습니다",
            "retry": "🔄 재생성을 시작합니다",
            "edit": "✏️ 수정 요청이 접수되었습니다",
        }
        return texts.get(action, "처리되었습니다")

    def request_approval(
        self,
        step: str,
        job_id: str,
        caption: str,
        images: list[bytes] = None,
        video_path: str = None,
        timeout: int = 600,
    ) -> tuple[ApprovalResult, str]:
        """
        Send results to Telegram and wait for approval.

        Args:
            step: Pipeline step name (image_gen, video_gen, edit, upload)
            job_id: Unique job identifier
            caption: Message text
            images: List of image bytes to send
            video_path: Path to video file
            timeout: Max wait time in seconds

        Returns:
            (ApprovalResult, edit_text)
            edit_text is only set when result is EDIT
        """
        if not self.token or not self.chat_id:
            print("[Approval] Telegram not configured, auto-approving")
            return ApprovalResult.APPROVE, ""

        self._start_polling()

        # Register pending approval
        self._pending[job_id] = {"result": None, "edit_text": ""}

        # Build inline keyboard
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "✅ 통과", "callback_data": f"approve:{job_id}"},
                    {"text": "🔄 재생성", "callback_data": f"retry:{job_id}"},
                    {"text": "✏️ 수정요청", "callback_data": f"edit:{job_id}"},
                ]
            ]
        }

        # Send media with approval buttons
        if images:
            self._send_photo_group(images, caption, keyboard)
        elif video_path:
            self._send_video(video_path, caption, keyboard)
        else:
            self._send_message(caption, keyboard)

        # Wait for response
        print(f"[Approval] Waiting for {step} approval (job: {job_id[:8]}), timeout: {timeout}s")
        start = time.time()
        while time.time() - start < timeout:
            pending = self._pending.get(job_id, {})
            result = pending.get("result")

            if result is not None:
                edit_text = pending.get("edit_text", "")
                del self._pending[job_id]
                print(f"[Approval] {step} result: {result}")
                return result, edit_text

            time.sleep(2)

        # Timeout
        del self._pending[job_id]
        print(f"[Approval] {step} timed out")
        return ApprovalResult.APPROVE, ""

    def _send_message(self, text: str, keyboard: dict = None):
        """Send text message with optional keyboard."""
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "Markdown",
        }
        if keyboard:
            payload["reply_markup"] = json.dumps(keyboard)
        try:
            httpx.post(f"{self.BASE_URL}/sendMessage", json=payload, timeout=10)
        except Exception as e:
            print(f"[Approval] sendMessage error: {e}")

    def _send_photo_group(self, images: list[bytes], caption: str, keyboard: dict):
        """Send multiple images as a media group with caption."""
        if not images:
            return

        # Send first image with caption + keyboard
        try:
            resp = httpx.post(f"{self.BASE_URL}/sendPhoto", data={
                "chat_id": self.chat_id,
                "caption": caption,
                "parse_mode": "Markdown",
                "reply_markup": json.dumps(keyboard),
            }, files={
                "photo": ("result.png", images[0], "image/png"),
            }, timeout=30)

            # Send remaining images without keyboard
            for i, img in enumerate(images[1:], 1):
                httpx.post(f"{self.BASE_URL}/sendPhoto", data={
                    "chat_id": self.chat_id,
                    "caption": f"이미지 {i+1}/{len(images)}",
                }, files={
                    "photo": (f"result_{i}.png", img, "image/png"),
                }, timeout=30)
        except Exception as e:
            print(f"[Approval] sendPhoto error: {e}")

    def _send_video(self, video_path: str, caption: str, keyboard: dict):
        """Send video file with caption and keyboard."""
        try:
            with open(video_path, "rb") as f:
                httpx.post(f"{self.BASE_URL}/sendVideo", data={
                    "chat_id": self.chat_id,
                    "caption": caption,
                    "parse_mode": "Markdown",
                    "reply_markup": json.dumps(keyboard),
                }, files={
                    "video": ("result.mp4", f, "video/mp4"),
                }, timeout=60)
        except Exception as e:
            print(f"[Approval] sendVideo error: {e}")

    def notify_step(self, step: str, message: str):
        """Send a simple notification (no approval buttons)."""
        self._send_message(f"*[{step}]* {message}")
