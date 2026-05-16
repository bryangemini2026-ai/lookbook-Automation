"""
24-hour Autonomous Cycle Scheduler.

Runs scheduled tasks at specific times.
Inspired by Connect AI's report_schedule.json pattern.

Usage:
    from scheduler import AutoScheduler
    scheduler = AutoScheduler(redis_client)
    scheduler.run_forever()
"""

import json
import os
import time
from datetime import datetime

import redis

from config import settings
from modules.briefing import BriefingModule


# ── Default Schedule ──

DEFAULT_SCHEDULE = {
    "entries": [
        {
            "id": "morning-brief",
            "label": "모닝 브리핑",
            "hour": 9,
            "minute": 0,
            "days": [0, 1, 2, 3, 4, 5, 6],  # 0=Mon, 6=Sun
            "action": "briefing",
            "args": {"type": "morning"},
            "enabled": True,
        },
        {
            "id": "evening-report",
            "label": "이브닝 리포트",
            "hour": 18,
            "minute": 0,
            "days": [0, 1, 2, 3, 4, 5, 6],
            "action": "briefing",
            "args": {"type": "evening"},
            "enabled": True,
        },
        {
            "id": "queue-retry",
            "label": "실패 큐 재시도",
            "hour": 3,
            "minute": 0,
            "days": [0, 1, 2, 3, 4, 5, 6],
            "action": "retry_failed",
            "args": {},
            "enabled": True,
        },
        {
            "id": "brain-trend-collect",
            "label": "트렌드 데이터 수집",
            "hour": 2,
            "minute": 0,
            "days": [0, 1, 2, 3, 4, 5, 6],
            "action": "collect_trends",
            "args": {},
            "enabled": True,
        },
    ]
}

SCHEDULE_PATH = os.path.join(settings.STORAGE_BASE, "schedule.json")


class AutoScheduler:
    """
    Cron-style scheduler for autonomous tasks.
    Checks every 60 seconds if any scheduled task should run.
    """

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.briefing = BriefingModule(redis_client)
        self.schedule = self._load_schedule()
        self._last_run: dict[str, str] = {}  # entry_id -> last run date

    def _load_schedule(self) -> dict:
        """Load schedule from file or use defaults."""
        if os.path.exists(SCHEDULE_PATH):
            with open(SCHEDULE_PATH) as f:
                return json.load(f)
        # Write defaults
        os.makedirs(os.path.dirname(SCHEDULE_PATH), exist_ok=True)
        with open(SCHEDULE_PATH, "w") as f:
            json.dump(DEFAULT_SCHEDULE, f, indent=2, ensure_ascii=False)
        return DEFAULT_SCHEDULE

    def _save_schedule(self):
        with open(SCHEDULE_PATH, "w") as f:
            json.dump(self.schedule, f, indent=2, ensure_ascii=False)

    def run_forever(self):
        """Main loop: check every 60 seconds."""
        print("AutoScheduler started.")
        self._print_schedule()

        while True:
            now = datetime.utcnow()
            self._check_and_run(now)
            time.sleep(60)

    def _check_and_run(self, now: datetime):
        """Check if any scheduled task should run now."""
        current_hour = now.hour
        current_minute = now.minute
        current_day = now.weekday()  # 0=Mon, 6=Sun
        today_key = now.strftime("%Y-%m-%d")

        for entry in self.schedule.get("entries", []):
            if not entry.get("enabled", True):
                continue

            entry_id = entry["id"]

            # Check day of week
            if current_day not in entry.get("days", []):
                continue

            # Check time (within 1-minute window)
            if entry["hour"] != current_hour or entry["minute"] != current_minute:
                continue

            # Skip if already run today
            if self._last_run.get(entry_id) == today_key:
                continue

            # Execute
            print(f"[Scheduler] Running: {entry['label']} ({entry_id})")
            try:
                self._execute(entry)
                self._last_run[entry_id] = today_key
                print(f"[Scheduler] Completed: {entry['label']}")
            except Exception as e:
                print(f"[Scheduler] Failed: {entry['label']} — {e}")

    def _execute(self, entry: dict):
        """Execute a scheduled task."""
        action = entry["action"]
        args = entry.get("args", {})

        if action == "briefing":
            self.briefing.send_briefing(type=args.get("type", "morning"))

        elif action == "retry_failed":
            self._retry_failed_jobs()

        elif action == "collect_trends":
            self._collect_trends()

        else:
            print(f"[Scheduler] Unknown action: {action}")

    def _retry_failed_jobs(self):
        """Move failed jobs back to pending queue."""
        failed_key = "lookbook:queue:failed"
        pending_key = "lookbook:queue:pending"

        count = 0
        while True:
            raw = self.redis.rpoplpush(failed_key, pending_key)
            if raw is None:
                break
            count += 1

        if count > 0:
            print(f"[Scheduler] Retried {count} failed jobs")
        else:
            print("[Scheduler] No failed jobs to retry")

    def _collect_trends(self):
        """Collect trend data and save to brain."""
        from modules.brain import BrainModule
        brain = BrainModule()
        brain.collect_daily_trends()

    def _print_schedule(self):
        """Print current schedule."""
        print("\n=== Schedule ===")
        for entry in self.schedule.get("entries", []):
            status = "ON" if entry.get("enabled", True) else "OFF"
            days = ",".join(str(d) for d in entry.get("days", []))
            print(f"  [{status}] {entry['label']} — {entry['hour']:02d}:{entry['minute']:02d} (days: {days})")
        print()

    def add_entry(self, entry: dict):
        """Add a new scheduled task."""
        self.schedule["entries"].append(entry)
        self._save_schedule()

    def toggle_entry(self, entry_id: str, enabled: bool):
        """Enable/disable a scheduled task."""
        for entry in self.schedule["entries"]:
            if entry["id"] == entry_id:
                entry["enabled"] = enabled
                self._save_schedule()
                return
        raise ValueError(f"Entry not found: {entry_id}")
