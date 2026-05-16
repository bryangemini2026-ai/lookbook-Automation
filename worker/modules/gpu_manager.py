import subprocess
import time

import redis
import httpx


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
            capture_output=True,
            text=True,
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
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(f"GPU: Switch failed: {result.stderr}")
            return False

        # Wait for ComfyUI API to be ready
        return self._wait_for_ready(required)

    def _wait_for_ready(self, server: str, timeout: int = 60) -> bool:
        """Wait for ComfyUI API to respond."""
        port = 8188 if server == "image" else 8288
        url = f"http://localhost:{port}/system_stats"

        for _ in range(timeout):
            try:
                resp = httpx.get(url, timeout=2)
                if resp.status_code == 200:
                    print(f"GPU: {server} server ready on :{port}")
                    return True
            except httpx.ConnectError:
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
