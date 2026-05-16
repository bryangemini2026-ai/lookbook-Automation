"""
Standalone scheduler process.

Run separately from the main PipelineWorker:
    python run_scheduler.py

Handles:
- Morning briefing (09:00)
- Evening report (18:00)
- Failed job retry (03:00)
- Trend collection (02:00)
"""

import redis
from config import settings
from scheduler import AutoScheduler


def main():
    r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)
    scheduler = AutoScheduler(r)
    scheduler.run_forever()


if __name__ == "__main__":
    main()
