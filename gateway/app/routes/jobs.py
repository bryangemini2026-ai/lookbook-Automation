import json
import uuid

import redis
from fastapi import APIRouter, HTTPException

from app.config import settings
from app.db import get_db
from app.schemas import JobCreate, JobResponse

router = APIRouter()
r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)

QUEUE_PENDING = "lookbook:queue:pending"


@router.post("/", response_model=JobResponse)
def create_job(job: JobCreate):
    """Create a new job and enqueue to Redis."""
    job_id = str(uuid.uuid4())

    # Store in SQLite
    db = get_db()
    db.execute(
        "INSERT INTO jobs (id, status, type, prompt, negative_prompt, workflow, params) VALUES (?,?,?,?,?,?,?)",
        (job_id, "pending", job.type, job.prompt, job.negative_prompt, job.workflow, json.dumps(job.params)),
    )
    db.commit()
    db.close()

    # Enqueue to Redis pending queue
    r.lpush(QUEUE_PENDING, json.dumps({
        "id": job_id,
        "type": job.type,
        "prompt": job.prompt,
        "negative_prompt": job.negative_prompt,
        "workflow": job.workflow,
        "params": job.params,
        "upscale": job.upscale,
        "face_fix": job.face_fix,
        "make_reel": job.make_reel,
        "reel_style": job.reel_style,
        "platforms": job.platforms,
    }))

    return JobResponse(id=job_id, status="pending")


@router.get("/")
def list_jobs(limit: int = 20, offset: int = 0, status: str | None = None):
    """List jobs with optional status filter."""
    db = get_db()
    if status:
        rows = db.execute(
            "SELECT * FROM jobs WHERE status=? ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (status, limit, offset),
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
    db.close()
    return [dict(row) for row in rows]


@router.get("/{job_id}")
def get_job(job_id: str):
    """Get job detail with live progress from Redis."""
    db = get_db()
    row = db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    db.close()

    if not row:
        raise HTTPException(status_code=404, detail="Job not found")

    result = dict(row)

    # Merge with live Redis state (stage, progress, etc.)
    live = r.hgetall(f"job:{job_id}")
    if live:
        result.update(live)

    return result


@router.delete("/{job_id}")
def cancel_job(job_id: str):
    """Cancel a pending or running job."""
    r.hset(f"job:{job_id}", mapping={"status": "cancelled"})
    db = get_db()
    db.execute("UPDATE jobs SET status='cancelled', updated_at=datetime('now') WHERE id=?", (job_id,))
    db.commit()
    db.close()
    return {"id": job_id, "status": "cancelled"}


@router.post("/{job_id}/retry")
def retry_job(job_id: str):
    """Retry a failed job."""
    db = get_db()
    row = db.execute("SELECT * FROM jobs WHERE id=? AND status='failed'", (job_id,)).fetchone()
    if not row:
        db.close()
        raise HTTPException(status_code=400, detail="Job not found or not in failed state")

    job = dict(row)
    db.execute("UPDATE jobs SET status='pending', error=NULL, updated_at=datetime('now') WHERE id=?", (job_id,))
    db.commit()
    db.close()

    # Re-enqueue
    r.lpush(QUEUE_PENDING, json.dumps({
        "id": job_id,
        "type": job["type"],
        "prompt": job["prompt"],
        "negative_prompt": job["negative_prompt"],
        "workflow": job["workflow"],
        "params": json.loads(job["params"]) if job["params"] else {},
    }))

    return {"id": job_id, "status": "pending"}
