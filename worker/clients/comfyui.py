import json
import uuid
import time
import httpx


class ComfyUIClient:
    """ComfyUI HTTP API client for headless workflow execution."""

    def __init__(self, host: str = "http://localhost:8188"):
        self.host = host.rstrip("/")
        self.client_id = str(uuid.uuid4())

    def queue_prompt(self, workflow: dict) -> str:
        """Submit workflow to ComfyUI queue. Returns prompt_id."""
        resp = httpx.post(f"{self.host}/prompt", json={
            "prompt": workflow,
            "client_id": self.client_id,
        }, timeout=10)
        resp.raise_for_status()
        return resp.json()["prompt_id"]

    def get_history(self, prompt_id: str) -> dict:
        """Get generation history/result for a prompt."""
        resp = httpx.get(f"{self.host}/history/{prompt_id}", timeout=10)
        resp.raise_for_status()
        return resp.json()

    def get_progress(self, prompt_id: str) -> dict | None:
        """Get current progress. Returns None if not available."""
        try:
            resp = httpx.get(f"{self.host}/history/{prompt_id}", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if prompt_id in data:
                    return data[prompt_id]
        except httpx.ConnectError:
            pass
        return None

    def download_image(self, filename: str, subfolder: str = "", folder_type: str = "output") -> bytes:
        """Download generated image from ComfyUI."""
        resp = httpx.get(f"{self.host}/view", params={
            "filename": filename,
            "subfolder": subfolder,
            "type": folder_type,
        }, timeout=30)
        resp.raise_for_status()
        return resp.content

    def wait_for_completion(self, prompt_id: str, timeout: int = 300) -> list[bytes]:
        """Wait for workflow completion and return output images."""
        start = time.time()
        while time.time() - start < timeout:
            history = self.get_progress(prompt_id)
            if history and "outputs" in history:
                # Collect all output images
                images = []
                for node_id, node_output in history["outputs"].items():
                    if "images" in node_output:
                        for img_info in node_output["images"]:
                            img_bytes = self.download_image(
                                img_info["filename"],
                                img_info.get("subfolder", ""),
                                img_info.get("type", "output"),
                            )
                            images.append(img_bytes)
                return images
            time.sleep(2)

        raise TimeoutError(f"ComfyUI job {prompt_id} timed out after {timeout}s")

    def execute_workflow(self, workflow: dict, timeout: int = 300) -> list[bytes]:
        """Submit workflow and wait for completion. Returns output images."""
        prompt_id = self.queue_prompt(workflow)
        print(f"  ComfyUI: queued prompt {prompt_id[:8]}...")
        return self.wait_for_completion(prompt_id, timeout)

    def is_alive(self) -> bool:
        """Check if ComfyUI server is responding."""
        try:
            resp = httpx.get(f"{self.host}/system_stats", timeout=3)
            return resp.status_code == 200
        except httpx.ConnectError:
            return False

    def free_memory(self):
        """Request ComfyUI to free unused VRAM."""
        try:
            httpx.post(f"{self.host}/free", json={"unload_models": True, "free_memory": True}, timeout=5)
        except Exception:
            pass
