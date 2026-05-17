"""
System routes: version info, deploy webhook, health.
"""

import os
import subprocess
import hmac
from datetime import datetime

from dotenv import load_dotenv
from fastapi import APIRouter, Request, HTTPException

# Load .env from project root
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))

router = APIRouter()

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
VERSION_FILE = os.path.join(PROJECT_ROOT, "VERSION")
DEPLOY_SCRIPT = os.path.join(PROJECT_ROOT, "scripts", "deploy.sh")


def _get_deploy_token() -> str:
    """Read deploy token from env (re-reads each time for hot-reload)."""
    return os.getenv("DEPLOY_TOKEN", "")


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
    deploy_token = _get_deploy_token()

    # Verify token (skip only if no token is configured)
    if deploy_token:
        token = request.headers.get("X-Deploy-Token", "")
        if not token:
            raise HTTPException(status_code=401, detail="Missing X-Deploy-Token header")
        if not hmac.compare_digest(token, deploy_token):
            raise HTTPException(status_code=403, detail="Invalid deploy token")
    else:
        print("[Deploy] WARNING: DEPLOY_TOKEN not set — webhook is unsecured!")

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
