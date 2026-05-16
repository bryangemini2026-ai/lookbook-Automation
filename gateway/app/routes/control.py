import os
import subprocess

from fastapi import APIRouter

router = APIRouter()

GUARD_SCRIPT = "/opt/lookbook/scripts/gpu-guard.sh"
# Fallback: resolve relative to project root
if not os.path.exists(GUARD_SCRIPT):
    _PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    GUARD_SCRIPT = os.path.join(_PROJECT_ROOT, "scripts", "gpu-guard.sh")


def _run_guard(action: str, arg: str = "") -> dict:
    """Run gpu-guard.sh with error handling."""
    if not os.path.exists(GUARD_SCRIPT):
        return {"success": False, "output": f"gpu-guard.sh not found at {GUARD_SCRIPT}"}
    try:
        cmd = [GUARD_SCRIPT, action]
        if arg:
            cmd.append(arg)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return {"success": result.returncode == 0, "output": result.stdout}
    except Exception as e:
        return {"success": False, "output": str(e)}


@router.get("/gpu/status")
def gpu_status():
    """Get GPU server status."""
    # Try nvidia-smi directly as fallback
    if not os.path.exists(GUARD_SCRIPT):
        try:
            smi = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.used,memory.total,temperature.gpu", "--format=csv"],
                capture_output=True, text=True, timeout=5,
            )
            return {"output": smi.stdout if smi.returncode == 0 else "nvidia-smi not available"}
        except FileNotFoundError:
            return {"output": "GPU not available (no nvidia-smi, no gpu-guard.sh)"}
    return _run_guard("status")


@router.post("/gpu/start/{server}")
def start_server(server: str):
    """Start image or video ComfyUI server."""
    if server not in ("image", "video"):
        return {"error": "server must be 'image' or 'video'"}
    try:
        result = subprocess.run(
            ["sudo", "systemctl", "start", f"comfyui-{server}"],
            capture_output=True, text=True, timeout=10,
        )
        return {"success": result.returncode == 0, "output": result.stdout}
    except Exception as e:
        return {"success": False, "output": str(e)}


@router.post("/gpu/stop/{server}")
def stop_server(server: str):
    """Stop image or video ComfyUI server."""
    if server not in ("image", "video"):
        return {"error": "server must be 'image' or 'video'"}
    try:
        result = subprocess.run(
            ["sudo", "systemctl", "stop", f"comfyui-{server}"],
            capture_output=True, text=True, timeout=10,
        )
        return {"success": result.returncode == 0}
    except Exception as e:
        return {"success": False, "output": str(e)}


@router.post("/gpu/switch/{target}")
def switch_server(target: str):
    """Switch to target server (stops the other one first, cleans VRAM)."""
    if target not in ("image", "video"):
        return {"error": "target must be 'image' or 'video'"}
    return _run_guard("switch", target)


@router.get("/queue")
def queue_status():
    """Get Redis queue depths."""
    import redis
    from app.config import settings
    r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)

    return {
        "pending": r.llen("lookbook:queue:pending"),
        "running": r.llen("lookbook:queue:running"),
        "failed": r.llen("lookbook:queue:failed"),
    }
