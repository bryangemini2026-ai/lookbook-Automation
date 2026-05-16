"""
System routes: version info, deploy webhook, health.
"""

import os
import subprocess
import hashlib
import hmac
from datetime import datetime

from fastapi import APIRouter, Request, HTTPException
from app.config import settings

router = APIRouter()

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
VERSION_FILE = os.path.join(PROJECT_ROOT, "VERSION")
DEPLOY_SCRIPT = os.path.join(PROJECT_ROOT, "scripts", "deploy.sh")

# Deploy token from env (set in .env)
DEPLOY_TOKEN = os.getenv("DEPLOY_TOKEN", "")


def _read_version() -> dict:
    """Read VERSION file."""
    if not os.path.exists(VERSION_FILE):
        return {"version": "unknown", "timestamp": "", "sha": ""}

    with open(VERSION_FILE) as f:
        lines = f.read().strip().split("\n")

    return {
        "version": lines[0] if len(lines) > 0 else "unknown",
        "timestamp": lines[1] if len(lines) > 1 else "",
        "sha": lines[2] if len(lines) > 2 else "",
    }


@router.get("/version")
def get_version():
    """Get current system version."""
    v = _read_version()
    # Also get git info
    try:
        commit = subprocess.run(
            ["git", "-C", PROJECT_ROOT, "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        branch = subprocess.run(
            ["git", "-C", PROJECT_ROOT, "branch", "--show-current"],
            capture_output=True, text=True, timeout=5,
        )
        v["commit"] = commit.stdout.strip() if commit.returncode == 0 else "unknown"
        v["branch"] = branch.stdout.strip() if branch.returncode == 0 else "unknown"
    except Exception:
        v["commit"] = "unknown"
        v["branch"] = "unknown"

    v["server_time"] = datetime.utcnow().isoformat()
    return v


@router.post("/deploy")
async def deploy_webhook(request: Request):
    """
    Webhook endpoint for auto-deploy.
    GitHub Actions sends a POST here when a new version is released.

    Security: Requires X-Deploy-Token header matching DEPLOY_TOKEN env var.
    """
    # Verify token
    if DEPLOY_TOKEN:
        token = request.headers.get("X-Deploy-Token", "")
        if not hmac.compare_digest(token, DEPLOY_TOKEN):
            raise HTTPException(status_code=403, detail="Invalid deploy token")

    # Parse request
    try:
        body = await request.json()
    except Exception:
        body = {}

    version = body.get("version", "unknown")
    sha = body.get("sha", "unknown")

    print(f"[Deploy] Webhook received: version={version}, sha={sha}")

    # Run deploy script
    if os.path.exists(DEPLOY_SCRIPT):
        try:
            result = subprocess.run(
                ["bash", DEPLOY_SCRIPT],
                capture_output=True, text=True, timeout=120,
                cwd=PROJECT_ROOT,
            )
            return {
                "status": "deployed",
                "version": version,
                "output": result.stdout[-500:] if result.stdout else "",
                "errors": result.stderr[-500:] if result.stderr else "",
                "success": result.returncode == 0,
            }
        except subprocess.TimeoutExpired:
            return {"status": "timeout", "message": "Deploy script timed out"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    else:
        return {"status": "no_script", "message": f"Deploy script not found at {DEPLOY_SCRIPT}"}
