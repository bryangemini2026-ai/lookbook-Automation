"""
Daily Briefing System.

Generates and sends a daily summary via Telegram.
Inspired by Connect AI's ceo-report.md + secretary-telegram.md patterns.
"""

import json
import os
from datetime import datetime, timedelta

import redis

from config import settings
from clients.telegram import TelegramNotifier


class BriefingModule:
    """Generates daily briefings from job data and system status."""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.telegram = TelegramNotifier()

    def generate_morning_briefing(self) -> str:
        """
        Generate morning briefing (매일 오전 9시).
        Includes: yesterday's results, today's queue, system status.
        """
        now = datetime.utcnow()
        yesterday = now - timedelta(days=1)

        lines = [
            f"*Lookbook Morning Briefing*",
            f"_{now.strftime('%Y-%m-%d %H:%M')}_",
            "",
        ]

        # ── Yesterday's Stats ──
        yesterday_jobs = self._get_jobs_by_date(yesterday)
        completed = [j for j in yesterday_jobs if j.get("status") == "completed"]
        failed = [j for j in yesterday_jobs if j.get("status") == "failed"]

        lines.append("*Yesterday*")
        lines.append(f"  Completed: {len(completed)}")
        lines.append(f"  Failed: {len(failed)}")
        lines.append("")

        # ── Today's Queue ──
        pending = self.redis.llen("lookbook:queue:pending")
        running = self.redis.llen("lookbook:queue:running")
        failed_queue = self.redis.llen("lookbook:queue:failed")

        lines.append("*Queue Status*")
        lines.append(f"  Pending: {pending}")
        lines.append(f"  Running: {running}")
        lines.append(f"  Failed: {failed_queue}")
        lines.append("")

        # ── GPU Status ──
        gpu_info = self._get_gpu_info()
        if gpu_info:
            lines.append("*GPU*")
            lines.append(f"  {gpu_info}")
            lines.append("")

        # ── Top Performers ──
        if completed:
            lines.append("*Top Completed Jobs*")
            for j in completed[:3]:
                prompt = j.get("prompt", "N/A")[:40]
                lines.append(f"  - `{j['id'][:8]}` {prompt}")
            lines.append("")

        # ── Action Items ──
        if failed_queue > 0:
            lines.append("*Action Required*")
            lines.append(f"  {failed_queue} jobs in failed queue — review and retry")
            lines.append("")

        lines.append("_Have a productive day, 사장님!_")

        return "\n".join(lines)

    def generate_evening_report(self) -> str:
        """
        Generate evening report (매일 오후 6시).
        Includes: today's full results, performance summary.
        """
        now = datetime.utcnow()

        lines = [
            f"*Lookbook Daily Report*",
            f"_{now.strftime('%Y-%m-%d')}_",
            "",
        ]

        today_jobs = self._get_jobs_by_date(now)
        completed = [j for j in today_jobs if j.get("status") == "completed"]
        failed = [j for j in today_jobs if j.get("status") == "failed"]
        total_images = sum(1 for j in completed if "raw_images" in str(j.get("result_urls", "")))
        total_reels = sum(1 for j in completed if "video" in str(j.get("result_urls", "")))

        # ── Summary ──
        lines.append("*Today's Summary*")
        lines.append(f"  Jobs completed: {len(completed)}")
        lines.append(f"  Jobs failed: {len(failed)}")
        lines.append(f"  Images generated: {total_images}")
        lines.append(f"  Reels created: {total_reels}")
        lines.append("")

        # ── Completed Details ──
        if completed:
            lines.append("*Completed Jobs*")
            for j in completed:
                prompt = j.get("prompt", "N/A")[:50]
                workflow = j.get("workflow", "")
                lines.append(f"  - `{j['id'][:8]}` {workflow} — {prompt}")
            lines.append("")

        # ── Failed Details ──
        if failed:
            lines.append("*Failed Jobs*")
            for j in failed:
                error = j.get("error", "unknown")[:60]
                lines.append(f"  - `{j['id'][:8]}` {error}")
            lines.append("")

        # ── Recommendations ──
        lines.append("*Tomorrow Suggestions*")
        if len(failed) > len(completed):
            lines.append("  - Failure rate high — check GPU memory and ComfyUI stability")
        if pending := self.redis.llen("lookbook:queue:pending"):
            lines.append(f"  - {pending} jobs still pending — consider running overnight")
        if not completed and not failed:
            lines.append("  - No jobs today. Drop images in inbox to get started!")

        return "\n".join(lines)

    def send_briefing(self, type: str = "morning"):
        """Generate and send briefing via Telegram."""
        if type == "morning":
            text = self.generate_morning_briefing()
        else:
            text = self.generate_evening_report()

        self.telegram.send_message(text)
        print(f"Briefing sent: {type}")

    def _get_jobs_by_date(self, date: datetime) -> list[dict]:
        """Get all jobs for a specific date from Redis."""
        date_str = date.strftime("%Y-%m-%d")
        jobs = []

        # Scan Redis for job hashes
        for key in self.redis.scan_iter("job:*"):
            if key.startswith("job:queue"):
                continue
            data = self.redis.hgetall(key)
            if data:
                created = data.get("created_at", "")
                if date_str in created:
                    data["id"] = key.replace("job:", "")
                    jobs.append(data)

        return jobs

    def _get_gpu_info(self) -> str:
        """Get GPU memory info via nvidia-smi."""
        try:
            import subprocess
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=memory.used,memory.total,temperature.gpu",
                 "--format=csv,noheader"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return ""
