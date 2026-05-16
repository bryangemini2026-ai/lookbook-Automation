# Lookbook SNS Automation — Architecture v3.0

> **Design Philosophy**: Local AI production workstation. Single GPU server. Manual control. Maximum stability. Zero cloud dependency.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Tech Stack](#2-tech-stack)
3. [Dual ComfyUI Strategy](#3-dual-comfyui-strategy)
4. [GPU Mutual Exclusion](#4-gpu-mutual-exclusion)
5. [PipelineWorker](#5-pipelineworker)
6. [FastAPI Gateway](#6-fastapi-gateway)
7. [Dashboard](#7-dashboard)
8. [Watch-Folder & Samba](#8-watch-folder--samba)
9. [Telegram Bot](#9-telegram-bot)
10. [Storage & Database](#10-storage--database)
11. [Folder Structure](#11-folder-structure)
12. [API Structure](#12-api-structure)
13. [Deployment](#13-deployment)
14. [MVP Roadmap](#14-mvp-roadmap)

---

## 1. Architecture Overview

### System Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                  Computer A — Ubuntu GPU Server (PRIMARY)           │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    GPU Control Layer                         │  │
│  │  ┌─────────────┐              ┌─────────────┐               │  │
│  │  │  ComfyUI    │   MUTUAL    │  ComfyUI    │               │  │
│  │  │  Image      │◄─EXCLUSION─►│  Video      │               │  │
│  │  │  :8188      │   (only 1   │  :8288      │               │  │
│  │  │             │  at a time) │             │               │  │
│  │  └─────────────┘              └─────────────┘               │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │  FastAPI     │  │  Redis       │  │  SQLite      │             │
│  │  :8000       │  │  :6379       │  │  (file)      │             │
│  └──────┬───────┘  └──────┬───────┘  └──────────────┘             │
│         │                  │                                        │
│  ┌──────┴──────────────────┴───────┐                               │
│  │       PipelineWorker            │                               │
│  │  (queue consumer, sequential)   │                               │
│  └──────────────┬──────────────────┘                               │
│                 │                                                   │
│  ┌──────────────┴──────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │  FFmpeg             │  │  Telegram    │  │  Samba Server    │ │
│  │  (reel maker)       │  │  Bot         │  │  :445            │ │
│  └─────────────────────┘  └──────────────┘  └──────────────────┘ │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Local Storage: /srv/lookbook/                              │  │
│  │  ├── inbox/       (Samba share, watch folder)               │  │
│  │  ├── outbox/      (generated results)                       │  │
│  │  ├── processed/   (archive)                                 │  │
│  │  ├── brand/       (logos, watermarks)                       │  │
│  │  └── bgm/         (background music)                        │  │
│  └──────────────────────────────────────────────────────────────┘  │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ Tailscale + Samba
                                │
┌───────────────────────────────┴─────────────────────────────────────┐
│                  Computer B — Windows Dashboard                     │
│                                                                     │
│  ┌───────────────────┐  ┌───────────────────┐                      │
│  │  React + Vite     │  │  Samba Mount      │                      │
│  │  Dashboard        │  │  \\\\A\lookbook   │                      │
│  │  :5173            │  │  → Z: drive       │                      │
│  └───────────────────┘  └───────────────────┘                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Communication Flow

```
Dashboard (B)                    GPU Server (A)
─────────────                    ──────────────
  │                                │
  ├─ HTTP API ────────────────────►│ FastAPI :8000
  │  (Tailscale)                   │   │
  │                                │   ├─ enqueue → Redis
  │                                │   ├─ state → SQLite
  │                                │   │
  │                                │   ▼
  │                                │ PipelineWorker
  │                                │   │
  │                                │   ├─► ComfyUI Image :8188
  │                                │   ├─► ComfyUI Video :8288
  │                                │   ├─► FFmpeg (reels)
  │                                │   └─► Telegram notify
  │                                │
  ├─ Samba (Z: drive) ────────────►│ /srv/lookbook/
  │  (drag & drop)                 │
  │                                │
  ◄──── Telegram alerts ──────────│ Telegram Bot
```

---

## 2. Tech Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| **GPU Engine (Image)** | ComfyUI bare metal :8188 | SDXL, Flux, IPAdapter, Upscale |
| **GPU Engine (Video)** | ComfyUI bare metal :8288 | AnimateDiff, video workflows |
| **API** | FastAPI (Python) | Runs on A, serves dashboard |
| **Queue** | Redis (bare metal on A) | RPUSH/BRPOPLPUSH with running/failed separation |
| **Database** | SQLite (file on A) | Job state, settings, schedules |
| **Pipeline** | Python (single process on A) | Sequential job execution |
| **Video Processing** | FFmpeg | Reel creation, zero GPU cost |
| **Frontend** | React + Vite + Tailwind (on B) | SPA dashboard |
| **Networking** | Tailscale | Secure A↔B connection |
| **File Sharing** | Samba | Windows-native Z: drive mount |
| **Notifications** | Telegram Bot | Direct on A, no cloud needed |
| **Storage** | Local disk on A | Samba-shared, optional R2 later |

### What is NOT used

- ~~AWS / Cloud servers~~
- ~~PostgreSQL~~
- ~~Ollama / Local LLM~~
- ~~Docker Compose multi-service~~
- ~~Celery~~
- ~~Next.js SSR~~
- ~~MinIO~~

---

## 3. Dual ComfyUI Strategy

### Why Two Separate Installations

| Problem | Solution |
|---------|----------|
| AnimateDiff nodes conflict with image nodes | Separate `custom_nodes/` |
| Different Python dependency versions | Separate `venv/` |
| Video needs different torch/xformers | Isolated environments |
| One server crashes → other unaffected | Independent processes |
| Need to restart one without affecting other | Separate systemd units |

### Installation Layout

```
/opt/comfyui/
├── image/                          # Image Server
│   ├── venv/                       # Python venv (image deps)
│   ├── main.py
│   ├── models/
│   │   ├── checkpoints/            # SDXL, Flux, RealVisXL
│   │   ├── loras/
│   │   ├── controlnet/
│   │   ├── upscale_models/         # RealESRGAN, UltraSharp
│   │   ├── ipadapter/
│   │   └── insightface/            # For face tools
│   ├── custom_nodes/
│   │   ├── ComfyUI-Manager/
│   │   ├── ComfyUI_IPAdapter_plus/
│   │   ├── comfyui-reactor-node/   # Face swap
│   │   ├── ComfyUI-Impact-Pack/    # FaceDetailer, detection
│   │   └── ComfyUI-KJNodes/        # Utilities
│   └── input/
│
└── video/                          # Video Server
    ├── venv/                       # Python venv (video deps)
    ├── main.py
    ├── models/
    │   ├── checkpoints/            # SD1.5 (AnimateDiff base)
    │   ├── animatediff/            # Motion modules
    │   ├── loras/
    │   └── controlnet/
    ├── custom_nodes/
    │   ├── ComfyUI-Manager/
    │   ├── ComfyUI-AnimateDiff-Evolved/
    │   ├── ComfyUI-VideoHelperSuite/
    │   └── ComfyUI-KJNodes/
    └── input/
```

### systemd Units

```ini
# /etc/systemd/system/comfyui-image.service
[Unit]
Description=ComfyUI Image Server
After=network.target

[Service]
Type=simple
User=lookbook
WorkingDirectory=/opt/comfyui/image
ExecStartPre=/opt/lookbook/scripts/gpu-guard.sh check image
ExecStart=/opt/comfyui/image/venv/bin/python main.py \
    --listen 0.0.0.0 --port 8188 \
    --use-split-cross-attention --force-fp16
ExecStopPost=/opt/lookbook/scripts/gpu-guard.sh cleanup image
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```ini
# /etc/systemd/system/comfyui-video.service
[Unit]
Description=ComfyUI Video Server
After=network.target

[Service]
Type=simple
User=lookbook
WorkingDirectory=/opt/comfyui/video
ExecStartPre=/opt/lookbook/scripts/gpu-guard.sh check video
ExecStart=/opt/comfyui/video/venv/bin/python main.py \
    --listen 0.0.0.0 --port 8288 \
    --use-split-cross-attention --force-fp16
ExecStopPost=/opt/lookbook/scripts/gpu-guard.sh cleanup video
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

---

## 4. GPU Mutual Exclusion

### The Rule

**RTX 3070 Ti 8GB can only run ONE ComfyUI server at a time.**

### GPU Guard Script

```bash
#!/bin/bash
# /opt/lookbook/scripts/gpu-guard.sh
#
# GPU mutual exclusion for dual ComfyUI servers.
# Ensures only one server occupies the GPU at a time.
#
# Called by systemd ExecStartPre/ExecStopPost.
# CRITICAL: systemd passes the 2nd argument ($2) as the caller identity.
#   ExecStartPre=/opt/lookbook/scripts/gpu-guard.sh check image
#   ExecStopPost=/opt/lookbook/scripts/gpu-guard.sh cleanup image
#
# Usage:
#   gpu-guard.sh check <image|video>    — pre-start: verify + lock
#   gpu-guard.sh cleanup <image|video>  — post-stop: unlock + VRAM cleanup
#   gpu-guard.sh switch <image|video>   — runtime: stop other + start target
#   gpu-guard.sh status                 — query current state

set -euo pipefail

ACTION="${1:-}"
CALLER="${2:-}"

IMAGE_LOCK="/tmp/comfyui-image.lock"
VIDEO_LOCK="/tmp/comfyui-video.lock"

# ── helper: kill leftover ComfyUI processes and free VRAM ──
force_cleanup_gpu() {
    local port="$1"  # 8188 or 8288

    # 1. Kill any python process listening on the given port
    local pids
    pids=$(fuser "${port}/tcp" 2>/dev/null | xargs || true)
    if [ -n "$pids" ]; then
        echo "gpu-guard: killing leftover processes on :${port} (PIDs: ${pids})"
        kill -9 $pids 2>/dev/null || true
        sleep 1
    fi

    # 2. Kill any orphan comfyui/python that still holds GPU memory
    #    Match by port in cmdline to avoid killing unrelated python processes
    pkill -9 -f "main.py.*--port ${port}" 2>/dev/null || true
    sleep 1

    # 3. Verify GPU memory is freed
    local vram_used
    vram_used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits 2>/dev/null || echo "0")
    if [ "$vram_used" -gt 500 ] 2>/dev/null; then
        echo "gpu-guard: WARNING — GPU still using ${vram_used}MB after cleanup"
    else
        echo "gpu-guard: GPU memory cleared (${vram_used}MB used)"
    fi
}

case "$ACTION" in
    # ── Pre-start check ──
    check)
        if [ -z "$CALLER" ]; then
            echo "ERROR: usage: gpu-guard.sh check <image|video>"
            exit 1
        fi

        # Check if the OTHER server holds the lock
        if [ "$CALLER" = "image" ] && [ -f "$VIDEO_LOCK" ]; then
            echo "ERROR: Video server is running. Stop it first or use 'switch image'."
            exit 1
        fi
        if [ "$CALLER" = "video" ] && [ -f "$IMAGE_LOCK" ]; then
            echo "ERROR: Image server is running. Stop it first or use 'switch video'."
            exit 1
        fi

        # Acquire lock
        touch "/tmp/comfyui-${CALLER}.lock"
        echo "gpu-guard: lock acquired for ${CALLER} server."
        ;;

    # ── Post-stop cleanup ──
    cleanup)
        if [ -z "$CALLER" ]; then
            echo "ERROR: usage: gpu-guard.sh cleanup <image|video>"
            exit 1
        fi

        # Release lock
        rm -f "/tmp/comfyui-${CALLER}.lock"
        echo "gpu-guard: lock released for ${CALLER} server."

        # Force-kill leftover processes and free VRAM
        if [ "$CALLER" = "image" ]; then
            force_cleanup_gpu 8188
        else
            force_cleanup_gpu 8288
        fi
        ;;

    # ── Runtime switch (stop other → clean → start target) ──
        switch)
        TARGET="${2:-}"
        if [ -z "$TARGET" ] || [[ "$TARGET" != "image" && "$TARGET" != "video" ]]; then
            echo "ERROR: usage: gpu-guard.sh switch <image|video>"
            exit 1
        fi

        if [ "$TARGET" = "image" ]; then
            echo "gpu-guard: switching to IMAGE server..."
            echo "gpu-guard: stopping video server..."
            systemctl stop comfyui-video 2>/dev/null || true
            sleep 2
            force_cleanup_gpu 8288
            echo "gpu-guard: starting image server..."
            systemctl start comfyui-image
        else
            echo "gpu-guard: switching to VIDEO server..."
            echo "gpu-guard: stopping image server..."
            systemctl stop comfyui-image 2>/dev/null || true
            sleep 2
            force_cleanup_gpu 8188
            echo "gpu-guard: starting video server..."
            systemctl start comfyui-video
        fi
        ;;

    # ── Status query ──
    status)
        echo "=== GPU Server Status ==="
        if [ -f "$IMAGE_LOCK" ]; then
            echo "Image server (:8188): RUNNING"
        else
            echo "Image server (:8188): STOPPED"
        fi
        if [ -f "$VIDEO_LOCK" ]; then
            echo "Video server (:8288): RUNNING"
        else
            echo "Video server (:8288): STOPPED"
        fi
        echo ""
        echo "=== GPU Memory ==="
        nvidia-smi --query-gpu=memory.used,memory.total,temperature.gpu --format=csv 2>/dev/null || echo "nvidia-smi unavailable"
        ;;

    *)
        echo "usage: gpu-guard.sh <check|cleanup|switch|status> [image|video]"
        exit 1
        ;;
esac
```

### PipelineWorker Integration

```python
# worker/modules/gpu_manager.py

import subprocess
import redis
import time

class GPUManager:
    """
    Manages ComfyUI server switching.
    Ensures only one server runs at a time on the 8GB GPU.
    """

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.GUARD_SCRIPT = "/opt/lookbook/scripts/gpu-guard.sh"

    def get_active_server(self) -> str | None:
        """Which server is currently running? 'image', 'video', or None."""
        result = subprocess.run(
            [self.GUARD_SCRIPT, "status"],
            capture_output=True, text=True
        )
        if "Image server (:8188): RUNNING" in result.stdout:
            return "image"
        elif "Video server (:8288): RUNNING" in result.stdout:
            return "video"
        return None

    def ensure_server(self, required: str) -> bool:
        """
        Ensure the required server is running.
        If the other server is active, switch with cleanup.

        Uses gpu-guard.sh switch which handles:
        1. Stopping the other server
        2. Killing leftover processes (pkill + fuser)
        3. Verifying VRAM is freed
        4. Starting the target server
        """
        active = self.get_active_server()

        if active == required:
            return True

        print(f"GPU: Switching to {required} server...")
        result = subprocess.run(
            [self.GUARD_SCRIPT, "switch", required],
            capture_output=True, text=True
        )

        if result.returncode != 0:
            print(f"GPU: Switch failed: {result.stderr}")
            return False

        # Wait for ComfyUI API to be ready
        return self._wait_for_ready(required)

    def _wait_for_ready(self, server: str, timeout: int = 60) -> bool:
        """Wait for ComfyUI API to respond."""
        import requests

        port = 8188 if server == "image" else 8288
        url = f"http://localhost:{port}/system_stats"

        for _ in range(timeout):
            try:
                resp = requests.get(url, timeout=2)
                if resp.status_code == 200:
                    print(f"GPU: {server} server ready on :{port}")
                    return True
            except requests.ConnectionError:
                pass
            time.sleep(1)

        print(f"GPU: {server} server timed out after {timeout}s")
        return False

    def stop_all(self):
        """Stop both servers."""
        subprocess.run(["systemctl", "stop", "comfyui-image"], capture_output=True)
        subprocess.run(["systemctl", "stop", "comfyui-video"], capture_output=True)
        subprocess.run([self.GUARD_SCRIPT, "cleanup", "image"], capture_output=True)
        subprocess.run([self.GUARD_SCRIPT, "cleanup", "video"], capture_output=True)
        print("GPU: All servers stopped.")
```

### Usage in PipelineWorker

```python
# worker/pipeline.py

def execute(self, job: Job):
    """Execute job with automatic GPU server management."""

    # Stage 1: Image generation (ensure image server)
    if job.type in ("lookbook", "upscale", "batch"):
        self.gpu.ensure_server("image")
        images = self.generation.generate(job)

    # Stage 2: Upscale (still image server)
    if job.upscale:
        # No switch needed, same server
        images = [self.upscale.upscale(img) for img in images]

    # Stage 3: Video (switch to video server)
    if job.make_reel:
        self.gpu.ensure_server("video")
        video = self.video.generate_reel(images, job)

    # Done — server stays running for next job
    # User can manually stop via dashboard/Telegram
```

---

## 5. PipelineWorker

### Architecture

```
PipelineWorker (single Python process)
│
├── main.py                 # Redis queue loop
├── pipeline.py             # Job orchestration
├── config.py               # Settings from .env
│
├── modules/
│   ├── prompt.py           # Optional prompt formatting (no LLM)
│   ├── generation.py       # ComfyUI Image server client
│   ├── upscale.py          # Real-ESRGAN via ComfyUI Image
│   ├── video.py            # ComfyUI Video server client + FFmpeg
│   ├── sns.py              # Platform formatting
│   └── gpu_manager.py      # Server switching logic
│
├── clients/
│   ├── comfyui.py          # ComfyUI HTTP API client
│   ├── telegram.py         # Telegram Bot API
│   └── storage.py          # Local filesystem + optional R2
│
├── utils/
│   ├── image.py            # PIL helpers
│   └── ffmpeg.py           # FFmpeg subprocess wrappers
│
└── watcher.py              # Watch folder daemon (inotify)
```

### main.py

```python
# worker/main.py

import redis
import json
import os
from pipeline import PipelineWorker
from config import settings

# Queue keys
QUEUE_PENDING = "lookbook:queue:pending"    # Jobs waiting to run
QUEUE_RUNNING  = "lookbook:queue:running"    # Currently executing
QUEUE_FAILED   = "lookbook:queue:failed"     # Failed (for retry/audit)

def main():
    r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)
    worker = PipelineWorker(r)

    print("PipelineWorker started. Waiting for jobs...")
    print(f"Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    print(f"Queue: {QUEUE_PENDING}")

    while True:
        # BRPOPLPUSH: atomically move job from pending → running
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
            # Move from running → failed queue
            r.lrem(QUEUE_RUNNING, 1, raw)
            r.lpush(QUEUE_FAILED, raw)
            # Update status
            r.hset(f"job:{job_id}", mapping={
                "status": "failed",
                "error": str(e)
            })
            worker.telegram.notify_error(job_id, str(e))

if __name__ == "__main__":
    main()
```

### Redis Queue Structure

```
lookbook:queue:pending    ← Dashboard/Watcher pushes here (LPUSH)
lookbook:queue:running    ← BRPOPLPUSH moves job here atomically
lookbook:queue:failed     ← Failed jobs moved here for retry/audit

Retry failed jobs:
  RPOPLPUSH lookbook:queue:failed lookbook:queue:pending

Check queue depths:
  LLEN lookbook:queue:pending
  LLEN lookbook:queue:running
  LLEN lookbook:queue:failed
```

### Pipeline Execution

```python
# worker/pipeline.py

class PipelineWorker:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.gpu = GPUManager(redis_client)
        self.comfyui_image = ComfyUIClient("http://localhost:8188")
        self.comfyui_video = ComfyUIClient("http://localhost:8288")
        self.generation = GenerationModule(self.comfyui_image)
        self.upscale = UpscaleModule(self.comfyui_image)
        self.video = VideoModule(self.comfyui_video)
        self.sns = SNSModule()
        self.telegram = TelegramNotifier()
        self.storage = LocalStorage()

    def execute(self, job: dict) -> dict:
        job_id = job["id"]
        results = {}

        # ── Stage 1: Image Generation ──
        self._update(job_id, "running", stage="generation")
        self.gpu.ensure_server("image")

        images = self.generation.generate(
            prompt=job["prompt"],
            negative=job.get("negative_prompt", ""),
            workflow=job.get("workflow", "lookbook_portrait"),
            params=job.get("params", {})
        )
        results["raw_images"] = self.storage.save_images(job_id, "raw", images)

        # ── Stage 2: Upscale ──
        if job.get("upscale", False):
            self._update(job_id, "running", stage="upscale")
            # Same server, no switch needed
            upscaled = [self.upscale.run(img) for img in images]
            results["upscaled_images"] = self.storage.save_images(job_id, "upscaled", upscaled)
            images = upscaled

        # ── Stage 3: Face Fix ──
        if job.get("face_fix", False):
            self._update(job_id, "running", stage="face_fix")
            fixed = [self.upscale.fix_faces(img) for img in images]
            results["fixed_images"] = self.storage.save_images(job_id, "fixed", fixed)
            images = fixed

        # ── Stage 4: Watermark ──
        if job.get("watermark", False):
            self._update(job_id, "running", stage="watermark")
            branded = [self.sns.add_watermark(img) for img in images]
            results["branded_images"] = self.storage.save_images(job_id, "branded", branded)

        # ── Stage 5: Video/Reel ──
        if job.get("make_reel", False):
            self._update(job_id, "running", stage="video")

            # Switch GPU to video server
            self.gpu.ensure_server("video")

            # Option A: AI video generation (AnimateDiff)
            if job.get("reel_type") == "ai_video":
                video = self.video.ai_generate(images[0], job.get("motion_prompt", ""))
            else:
                # Option B: FFmpeg reel (zero GPU cost)
                video = self.video.ffmpeg_reel(
                    images=images,
                    style=job.get("reel_style", "zoom_pan"),
                    duration=job.get("reel_duration", 3.0),
                    platform=job.get("platforms", ["instagram"])[0]
                )

            results["video"] = self.storage.save_video(job_id, "reel", video)

        # ── Stage 6: SNS Export ──
        self._update(job_id, "running", stage="export")
        exports = self.sns.export_for_platforms(
            images=images,
            video_path=results.get("video"),
            platforms=job.get("platforms", ["instagram"])
        )
        results["sns_exports"] = self.storage.save_exports(job_id, exports)

        # ── Stage 7: Notify ──
        self._update(job_id, "completed", results=results)
        self.telegram.notify_completion(job_id, results)

        return results

    def _update(self, job_id, status, **kwargs):
        """Update job status in Redis."""
        self.redis.hset(f"job:{job_id}", mapping={
            "status": status,
            **{k: json.dumps(v) if isinstance(v, (dict, list)) else str(v)
               for k, v in kwargs.items()}
        })
```

---

## 6. FastAPI Gateway

Single FastAPI app on Computer A. Serves both the dashboard (B) and Telegram bot.

### app/main.py

```python
# gateway/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.routes import jobs, workflows, control, settings, ws
from app.db import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()  # Create SQLite tables if needed
    yield

app = FastAPI(title="Lookbook Automation", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Dashboard on different host
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs.router, prefix="/api/jobs")
app.include_router(workflows.router, prefix="/api/workflows")
app.include_router(control.router, prefix="/api/control")
app.include_router(settings.router, prefix="/api/settings")
app.include_router(ws.router, prefix="/ws")

@app.get("/health")
def health():
    return {"status": "ok"}
```

### Routes

```python
# gateway/app/routes/jobs.py

from fastapi import APIRouter
import redis
import json
from app.db import get_db
from app.schemas import JobCreate, JobResponse

router = APIRouter()
r = redis.Redis(host="localhost", port=6379, decode_responses=True)

@router.post("/", response_model=JobResponse)
def create_job(job: JobCreate):
    """Create a new job and enqueue it."""
    import uuid
    job_id = str(uuid.uuid4())

    # Store in SQLite
    db = get_db()
    db.execute(
        "INSERT INTO jobs (id, status, type, prompt, workflow, params, created_at) VALUES (?,?,?,?,?,?,datetime('now'))",
        (job_id, "pending", job.type, job.prompt, job.workflow, json.dumps(job.params))
    )
    db.commit()

    # Enqueue to Redis pending queue
    r.lpush("lookbook:queue:pending", json.dumps({
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

    return {"id": job_id, "status": "pending"}

@router.get("/")
def list_jobs(limit: int = 20, offset: int = 0, status: str = None):
    """List jobs with optional status filter."""
    db = get_db()
    if status:
        rows = db.execute(
            "SELECT * FROM jobs WHERE status=? ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (status, limit, offset)
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset)
        ).fetchall()
    return [dict(row) for row in rows]

@router.get("/{job_id}")
def get_job(job_id: str):
    """Get job detail with current progress from Redis."""
    db = get_db()
    row = db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    if not row:
        return {"error": "not found"}, 404

    # Merge with live Redis state
    live = r.hgetall(f"job:{job_id}")
    result = dict(row)
    result.update(live)
    return result

@router.delete("/{job_id}")
def cancel_job(job_id: str):
    """Cancel a pending/running job."""
    r.hset(f"job:{job_id}", "status", "cancelled")
    db = get_db()
    db.execute("UPDATE jobs SET status='cancelled' WHERE id=?", (job_id,))
    db.commit()
    return {"id": job_id, "status": "cancelled"}
```

```python
# gateway/app/routes/control.py

from fastapi import APIRouter
import subprocess

router = APIRouter()

@router.get("/gpu/status")
def gpu_status():
    """Get GPU server status."""
    result = subprocess.run(
        ["/opt/lookbook/scripts/gpu-guard.sh", "status"],
        capture_output=True, text=True
    )
    return {"output": result.stdout}

@router.post("/gpu/start/{server}")
def start_server(server: str):
    """Start image or video ComfyUI server."""
    if server not in ("image", "video"):
        return {"error": "server must be 'image' or 'video'"}, 400

    result = subprocess.run(
        ["sudo", "systemctl", "start", f"comfyui-{server}"],
        capture_output=True, text=True
    )
    return {"success": result.returncode == 0, "output": result.stdout}

@router.post("/gpu/stop/{server}")
def stop_server(server: str):
    """Stop image or video ComfyUI server."""
    if server not in ("image", "video"):
        return {"error": "server must be 'image' or 'video'"}, 400

    result = subprocess.run(
        ["sudo", "systemctl", "stop", f"comfyui-{server}"],
        capture_output=True, text=True
    )
    return {"success": result.returncode == 0}

@router.post("/gpu/switch/{target}")
def switch_server(target: str):
    """Switch to target server (stops the other one first, cleans VRAM)."""
    if target not in ("image", "video"):
        return {"error": "target must be 'image' or 'video'"}, 400

    result = subprocess.run(
        ["/opt/lookbook/scripts/gpu-guard.sh", "switch", target],
        capture_output=True, text=True
    )
    return {"success": result.returncode == 0, "output": result.stdout}
```

### SQLite Schema

```python
# gateway/app/db.py

import sqlite3
import os

DB_PATH = os.getenv("SQLITE_PATH", "/opt/lookbook/data/lookbook.db")

def get_db():
    """
    Return a WAL-mode connection with busy timeout.
    - WAL: allows concurrent reads while PipelineWorker writes.
    - busy_timeout: waits up to 5s instead of throwing SQLITE_BUSY immediately.
    - journal_mode WAL + synchronous NORMAL = good balance of safety + speed.
    """
    conn = sqlite3.connect(DB_PATH, timeout=5)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            status TEXT DEFAULT 'pending',
            type TEXT DEFAULT 'lookbook',
            prompt TEXT,
            negative_prompt TEXT,
            workflow TEXT,
            params TEXT,
            result_urls TEXT,
            error TEXT,
            created_at TEXT,
            updated_at TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
        CREATE INDEX IF NOT EXISTS idx_jobs_created ON jobs(created_at DESC);

        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_template TEXT,
            cron_expr TEXT,
            active INTEGER DEFAULT 1,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );
    """)
    conn.commit()
    conn.close()
```

---

## 7. Dashboard

React + Vite SPA on Computer B. Calls FastAPI on Computer A via Tailscale.

### Pages

| Page | Route | Features |
|------|-------|----------|
| Home | `/` | GPU status, recent jobs, quick stats |
| Generate | `/generate` | Prompt, workflow select, params, submit |
| Queue | `/queue` | Job list, status, cancel/retry |
| Gallery | `/gallery` | Image grid, viewer, download |
| Reels | `/reels` | Video preview, reel maker controls |
| SNS | `/sns` | Platform settings, scheduled posts |
| Settings | `/settings` | GPU control, API keys, Telegram config |

### GPU Control Panel (Settings Page)

```tsx
// dashboard/src/components/GpuControl.tsx

import { useState, useEffect } from 'react'
import { api } from '../lib/api'

export function GpuControl() {
    const [status, setStatus] = useState<string>('')
    const [loading, setLoading] = useState(false)

    const refresh = async () => {
        const { data } = await api.get('/control/gpu/status')
        setStatus(data.output)
    }

    useEffect(() => { refresh() }, [])

    const startServer = async (server: 'image' | 'video') => {
        setLoading(true)
        await api.post(`/control/gpu/start/${server}`)
        setTimeout(refresh, 3000)
        setLoading(false)
    }

    const stopServer = async (server: 'image' | 'video') => {
        setLoading(true)
        await api.post(`/control/gpu/stop/${server}`)
        setTimeout(refresh, 2000)
        setLoading(false)
    }

    const switchTo = async (target: 'image' | 'video') => {
        setLoading(true)
        await api.post(`/control/gpu/switch/${target}`)
        setTimeout(refresh, 5000)
        setLoading(false)
    }

    return (
        <div className="space-y-4">
            <h2 className="text-xl font-bold">GPU Server Control</h2>

            <pre className="bg-gray-900 p-4 rounded text-sm">{status}</pre>

            <div className="grid grid-cols-2 gap-4">
                {/* Image Server */}
                <div className="border rounded p-4">
                    <h3 className="font-semibold mb-2">Image Server :8188</h3>
                    <div className="space-x-2">
                        <button
                            onClick={() => startServer('image')}
                            disabled={loading}
                            className="px-4 py-2 bg-green-600 text-white rounded"
                        >
                            Start
                        </button>
                        <button
                            onClick={() => stopServer('image')}
                            disabled={loading}
                            className="px-4 py-2 bg-red-600 text-white rounded"
                        >
                            Stop
                        </button>
                        <button
                            onClick={() => switchTo('image')}
                            disabled={loading}
                            className="px-4 py-2 bg-blue-600 text-white rounded"
                        >
                            Switch to Image
                        </button>
                    </div>
                </div>

                {/* Video Server */}
                <div className="border rounded p-4">
                    <h3 className="font-semibold mb-2">Video Server :8288</h3>
                    <div className="space-x-2">
                        <button
                            onClick={() => startServer('video')}
                            disabled={loading}
                            className="px-4 py-2 bg-green-600 text-white rounded"
                        >
                            Start
                        </button>
                        <button
                            onClick={() => stopServer('video')}
                            disabled={loading}
                            className="px-4 py-2 bg-red-600 text-white rounded"
                        >
                            Stop
                        </button>
                        <button
                            onClick={() => switchTo('video')}
                            disabled={loading}
                            className="px-4 py-2 bg-blue-600 text-white rounded"
                        >
                            Switch to Video
                        </button>
                    </div>
                </div>
            </div>

            <button
                onClick={refresh}
                className="px-4 py-2 bg-gray-600 text-white rounded"
            >
                Refresh Status
            </button>
        </div>
    )
}
```

---

## 8. Watch-Folder & Samba

### Samba Setup

```bash
# scripts/setup_samba.sh

sudo apt install -y samba

# Create folder structure
sudo mkdir -p /srv/lookbook/{inbox,outbox,processed,brand,bgm}
sudo chown -R lookbook:lookbook /srv/lookbook

# Samba config
cat << 'EOF' | sudo tee -a /etc/samba/smb.conf

[lookbook]
   path = /srv/lookbook
   browseable = yes
   writable = yes
   valid users = lookbook
   create mask = 0664
   directory mask = 0775
   force user = lookbook
   force group = lookbook
EOF

sudo smbpasswd -a lookbook
sudo systemctl restart smbd
```

### Watch Folder Daemon

```python
# worker/watcher.py

import inotify.adapters
import os
import redis
import json

WATCH_DIR = "/srv/lookbook/inbox"
QUEUE_KEY = "lookbook:queue:pending"
EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

def watch():
    r = redis.Redis(host="localhost", port=6379, decode_responses=True)
    i = inotify.adapters.Inotify()
    os.makedirs(WATCH_DIR, exist_ok=True)
    i.add_watch(WATCH_DIR)

    print(f"Watching {WATCH_DIR}...")

    for event in i.event_gen(yield_nones=False):
        (_, type_names, _, filename) = event
        if "IN_CLOSE_WRITE" not in type_names:
            continue
        if not any(filename.lower().endswith(ext) for ext in EXTENSIONS):
            continue

        filepath = os.path.join(WATCH_DIR, filename)
        config = _load_config()

        job = {
            "id": str(uuid.uuid4()),
            "source": "watch_folder",
            "source_file": filepath,
            **config  # default prompt, workflow, params, etc.
        }

        r.lpush(QUEUE_KEY, json.dumps(job))
        print(f"Auto-enqueued: {filename} → job {job['id']}")

def _load_config():
    path = "/srv/lookbook/watch_config.json"
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {
        "prompt": "professional fashion lookbook photo, studio lighting",
        "workflow": "lookbook_portrait",
        "upscale": True,
        "make_reel": False,
        "platforms": ["instagram"],
        "params": {"steps": 25, "cfg": 7.0, "width": 1024, "height": 1024}
    }
```

### systemd Service

```ini
# /etc/systemd/system/lookbook-watcher.service
[Unit]
Description=Lookbook Watch Folder Daemon
After=network.target redis.service

[Service]
Type=simple
User=lookbook
ExecStart=/opt/lookbook/worker/venv/bin/python /opt/lookbook/worker/watcher.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Folder Structure on Disk

```
/srv/lookbook/
├── inbox/                  # Samba share, drop files → auto job
│   └── (clothing images)
├── outbox/                 # Generated results
│   └── {job_id}/
│       ├── raw/            # Original ComfyUI outputs
│       ├── upscaled/       # Upscaled versions
│       ├── fixed/          # Face-fixed versions
│       ├── branded/        # Watermarked versions
│       ├── reel/           # Video files
│       └── sns/            # Platform-ready exports
│           ├── instagram/  # 1080x1080 or 1080x1350
│           ├── tiktok/     # 1080x1920
│           └── twitter/    # 1200x675
├── processed/              # Archive (completed jobs moved here)
├── brand/                  # Brand assets
│   ├── logo.png
│   └── watermark.png
├── bgm/                    # Background music for reels
│   └── *.mp3
└── watch_config.json       # Watch folder defaults
```

---

## 9. Telegram Bot

Runs directly on Computer A. No cloud dependency.

### Commands

| Command | Action |
|---------|--------|
| `/start` | Welcome message |
| `/status` | GPU status + queue length |
| `/image_start` | Start image server |
| `/image_stop` | Stop image server |
| `/video_start` | Start video server |
| `/video_stop` | Stop video server |
| `/switch_image` | Switch to image server |
| `/switch_video` | Switch to video server |
| `/queue` | Show pending jobs |
| `/generate <prompt>` | Quick generate |
| `/last` | Show last completed job results |

### Implementation

```python
# gateway/app/telegram_bot.py

import os
import redis
import subprocess
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GUARD_SCRIPT = "/opt/lookbook/scripts/gpu-guard.sh"

r = redis.Redis(host="localhost", port=6379, decode_responses=True)

async def cmd_status(update: Update, context):
    result = subprocess.run([GUARD_SCRIPT, "status"], capture_output=True, text=True)
    queue_len = r.llen("lookbook:queue")
    msg = f"```\n{result.stdout}\nQueue: {queue_len} jobs\n```"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def cmd_switch_image(update: Update, context):
    await update.message.reply_text("Switching to Image server...")
    subprocess.Popen([GUARD_SCRIPT, "switch", "system", "image"])
    await update.message.reply_text("Done. Image server starting on :8188")

async def cmd_switch_video(update: Update, context):
    await update.message.reply_text("Switching to Video server...")
    subprocess.Popen([GUARD_SCRIPT, "switch", "system", "video"])
    await update.message.reply_text("Done. Video server starting on :8288")

async def cmd_queue(update: Update, context):
    import json
    pending = r.llen("lookbook:queue:pending")
    running = r.llen("lookbook:queue:running")
    failed = r.llen("lookbook:queue:failed")

    lines = [f"Pending: {pending}", f"Running: {running}", f"Failed: {failed}", ""]

    jobs = []
    for raw in r.lrange("lookbook:queue:pending", 0, 4):
        job = json.loads(raw)
        jobs.append(f"  {job['id'][:8]}: {job.get('prompt', 'N/A')[:40]}")
    if jobs:
        lines.append("Next up:")
        lines.extend(jobs)

    await update.message.reply_text("\n".join(lines))

async def notify_completion(job_id: str, results: dict):
    """Called by PipelineWorker when a job completes."""
    import httpx
    # Send first image as preview
    images = results.get("raw_images", [])
    if images:
        with open(images[0], "rb") as f:
            await context.bot.send_photo(
                chat_id=CHAT_ID,
                photo=f,
                caption=f"Job {job_id[:8]} completed!\n{len(images)} images generated."
            )

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("switch_image", cmd_switch_image))
    app.add_handler(CommandHandler("switch_video", cmd_switch_video))
    app.add_handler(CommandHandler("queue", cmd_queue))
    app.run_polling()

if __name__ == "__main__":
    main()
```

---

## 10. Storage & Database

### SQLite (replaces PostgreSQL)

```
/opt/lookbook/data/lookbook.db

Tables:
  jobs         — id, status, type, prompt, workflow, params, results, timestamps
  schedules    — id, job_template (JSON), cron_expr, active
  settings     — key-value pairs
```

**Backup**: Just copy the `.db` file. One command.

```bash
# Backup
cp /opt/lookbook/data/lookbook.db /srv/lookbook/backup/lookbook_$(date +%Y%m%d).db

# Restore
cp /srv/lookbook/backup/lookbook_20260517.db /opt/lookbook/data/lookbook.db
```

### Local Storage

All generated assets live on `/srv/lookbook/` (Samba-shared).

**Backup strategy**: rsync to external drive or optional R2 sync.

```bash
# Optional: sync to Cloudflare R2 (future)
rclone sync /srv/lookbook/outbox/ r2:lookbook-backup/outbox/
```

---

## 11. Folder Structure

### Repository

```
lookbook-sns-automation/
├── .env.example
├── Makefile
├── README.md
│
├── gateway/                        # FastAPI app (runs on A)
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── db.py                   # SQLite connection + init
│   │   ├── schemas.py
│   │   ├── routes/
│   │   │   ├── jobs.py
│   │   │   ├── workflows.py
│   │   │   ├── control.py          # GPU start/stop/switch
│   │   │   ├── settings.py
│   │   │   └── ws.py
│   │   └── telegram_bot.py
│   └── alembic/
│
├── worker/                         # PipelineWorker (runs on A)
│   ├── requirements.txt
│   ├── main.py                     # Redis queue loop
│   ├── pipeline.py                 # Job orchestration
│   ├── config.py
│   ├── modules/
│   │   ├── generation.py           # ComfyUI Image client
│   │   ├── upscale.py
│   │   ├── video.py                # ComfyUI Video + FFmpeg
│   │   ├── sns.py                  # Platform formatting
│   │   └── gpu_manager.py          # Server switching
│   ├── clients/
│   │   ├── comfyui.py
│   │   ├── telegram.py
│   │   └── storage.py
│   ├── utils/
│   │   ├── image.py
│   │   └── ffmpeg.py
│   └── watcher.py                  # Watch folder daemon
│
├── dashboard/                      # React + Vite (runs on B)
│   ├── package.json
│   ├── vite.config.ts
│   ├── src/
│   │   ├── App.tsx
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Generate.tsx
│   │   │   ├── Queue.tsx
│   │   │   ├── Gallery.tsx
│   │   │   ├── Reels.tsx
│   │   │   ├── SNS.tsx
│   │   │   └── Settings.tsx
│   │   ├── components/
│   │   │   ├── GpuControl.tsx
│   │   │   ├── JobCard.tsx
│   │   │   ├── PromptInput.tsx
│   │   │   └── ImageGrid.tsx
│   │   ├── hooks/
│   │   │   └── useApi.ts
│   │   └── lib/
│   │       └── api.ts
│   └── index.html
│
├── workflows/                      # ComfyUI workflow JSON templates
│   ├── image/
│   │   ├── lookbook_portrait.json
│   │   ├── lookbook_full_body.json
│   │   ├── lookbook_flatlay.json
│   │   ├── upscale_4x.json
│   │   └── face_fix.json
│   └── video/
│       ├── animate_basic.json
│       └── animate_zoom.json
│
├── scripts/
│   ├── setup_gpu_server.sh         # Full A setup
│   ├── setup_samba.sh
│   ├── setup_comfyui_image.sh      # Install image ComfyUI
│   ├── setup_comfyui_video.sh      # Install video ComfyUI
│   ├── download_models.sh
│   ├── gpu-guard.sh                # GPU mutual exclusion
│   ├── comfyui-image.service       # systemd unit
│   ├── comfyui-video.service       # systemd unit
│   ├── lookbook-worker.service     # systemd unit
│   ├── lookbook-watcher.service    # systemd unit
│   └── lookbook-gateway.service    # systemd unit
│
└── docs/
    ├── architecture.md
    ├── deployment.md
    └── troubleshooting.md
```

---

## 12. API Structure

```
Base URL: http://100.64.0.1:8000/api

Health:
  GET  /health

Jobs:
  POST /jobs                          # Create + enqueue
  GET  /jobs                          # List (paginated, filterable)
  GET  /jobs/{id}                     # Detail + live progress
  DELETE /jobs/{id}                   # Cancel
  POST /jobs/{id}/retry               # Retry failed

GPU Control:
  GET  /control/gpu/status            # nvidia-smi + server status
  POST /control/gpu/start/{server}    # Start image or video
  POST /control/gpu/stop/{server}     # Stop image or video
  POST /control/gpu/switch/{target}   # Switch with auto-cleanup

Workflows:
  GET  /workflows                     # List presets
  GET  /workflows/{id}                # Detail

SNS:
  POST /sns/post                      # Post to platform
  POST /sns/schedule                  # Schedule post
  GET  /sns/scheduled                 # List scheduled

Settings:
  GET  /settings
  PUT  /settings

WebSocket:
  WS   /ws/status                     # Live job updates
```

---

## 13. Deployment

### Computer A Setup

```bash
# 1. System
sudo apt update && sudo apt install -y \
    python3.11 python3.11-venv python3-pip \
    git ffmpeg samba redis-server \
    nvidia-driver-535 inotify-tools

# 2. Tailscale
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up

# 3. Create user
sudo useradd -m -s /bin/bash lookbook
sudo usermod -aG sudo lookbook

# 4. Install ComfyUI Image Server
bash scripts/setup_comfyui_image.sh

# 5. Install ComfyUI Video Server
bash scripts/setup_comfyui_video.sh

# 6. Set up PipelineWorker
cd /opt/lookbook/worker
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 7. Set up FastAPI Gateway
cd /opt/lookbook/gateway
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 8. Set up Samba
bash scripts/setup_samba.sh

# 9. Install systemd services
sudo cp scripts/*.service /etc/systemd/system/
sudo systemctl daemon-reload

# 10. Start core services (NOT ComfyUI — manual start)
sudo systemctl enable redis-server
sudo systemctl enable lookbook-gateway
sudo systemctl enable lookbook-worker
sudo systemctl enable lookbook-watcher
sudo systemctl start redis-server
sudo systemctl start lookbook-gateway
sudo systemctl start lookbook-worker
sudo systemctl start lookbook-watcher

# 11. Download models
bash scripts/download_models.sh

# 12. Start ComfyUI when ready (manual)
sudo systemctl start comfyui-image
```

### Computer B Setup

```powershell
# 1. Install Tailscale (Windows app)

# 2. Map Samba
New-PSDrive -Name "Z" -PSProvider FileSystem -Root "\\100.64.0.1\lookbook" -Persist

# 3. Clone and run dashboard
cd ~\Projects
git clone <repo>
cd lookbook-sns-automation\dashboard
npm install
npm run dev
# → http://localhost:5173
```

---

## 14. MVP Roadmap

### Phase 1: Core (Week 1-2)

- [ ] Install ComfyUI Image Server bare metal on A
- [ ] Set up Redis on A
- [ ] Create FastAPI gateway with SQLite
- [ ] Implement PipelineWorker (generation module only)
- [ ] Test: `curl POST /jobs` → ComfyUI → image saved locally

### Phase 2: Control (Week 3)

- [ ] Install ComfyUI Video Server (separate)
- [ ] Implement GPU guard script + mutual exclusion
- [ ] Add GPU control endpoints (start/stop/switch)
- [ ] Add systemd services
- [ ] Test: switch between servers safely

### Phase 3: Dashboard (Week 4)

- [ ] React + Vite setup
- [ ] Generate page (prompt + workflow + submit)
- [ ] Queue page (job list + status)
- [ ] GPU control panel
- [ ] Gallery page (image viewer)

### Phase 4: Automation (Week 5)

- [ ] Samba setup + Windows mount
- [ ] Watch folder daemon
- [ ] FFmpeg reel maker
- [ ] Telegram bot (status + control commands)

### Phase 5: Polish (Week 6+)

- [ ] Upscale + FaceDetailer integration
- [ ] SNS posting (Instagram, Twitter)
- [ ] Watermark overlay
- [ ] Post scheduling
- [ ] More reel styles

---

*Architecture v3.0 — Local-first, single GPU, maximum stability*
*Last updated: 2026-05-17*
