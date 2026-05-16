import json

import redis

from config import settings
from pipeline import PipelineWorker

# Queue keys
QUEUE_PENDING = "lookbook:queue:pending"
QUEUE_RUNNING = "lookbook:queue:running"
QUEUE_FAILED = "lookbook:queue:failed"


def main():
    r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)
    worker = PipelineWorker(r)

    print("PipelineWorker started. Waiting for jobs...")
    print(f"Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    print(f"Queue: {QUEUE_PENDING}")

    while True:
        # BRPOPLPUSH: atomically move job from pending -> running
        # If worker crashes mid-job, Redis keeps it in running for inspection.
        raw = r.brpoplpush(QUEUE_PENDING, QUEUE_RUNNING, timeout=0)
        job_data = json.loads(raw)
        job_id = job_data.get("id", "unknown")

        print(f"\n[{job_id}] Received job: {job_data.get('type', 'unknown')}")

        try:
            result = worker.execute(job_data)
            print(f"[{job_id}] Completed. Results: {result}")
            # Remove from running queue on success
            r.lrem(QUEUE_RUNNING, 1, raw)

        except Exception as e:
            print(f"[{job_id}] FAILED: {e}")
            # Move from running -> failed queue
            r.lrem(QUEUE_RUNNING, 1, raw)
            r.lpush(QUEUE_FAILED, raw)
            # Update status
            r.hset(f"job:{job_id}", mapping={
                "status": "failed",
                "error": str(e),
            })
            worker.telegram.notify_error(job_id, str(e))


if __name__ == "__main__":
    main()
