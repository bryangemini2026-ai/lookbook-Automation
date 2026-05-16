import os
import uuid
from pathlib import Path

from config import settings


class LocalStorage:
    """Handles saving generated assets to local disk (Samba-shared)."""

    def __init__(self, base_dir: str = ""):
        self.base = base_dir or settings.STORAGE_BASE

    def _job_dir(self, job_id: str, subdir: str) -> Path:
        d = Path(self.base) / "outbox" / job_id / subdir
        d.mkdir(parents=True, exist_ok=True)
        return d

    def save_images(self, job_id: str, subdir: str, images: list[bytes]) -> list[str]:
        """Save image bytes to disk. Returns list of file paths."""
        d = self._job_dir(job_id, subdir)
        paths = []
        for i, img in enumerate(images):
            path = d / f"{i:03d}.png"
            path.write_bytes(img)
            paths.append(str(path))
        return paths

    def save_video(self, job_id: str, subdir: str, video: bytes) -> str:
        """Save video bytes to disk. Returns file path."""
        d = self._job_dir(job_id, subdir)
        path = d / "reel.mp4"
        path.write_bytes(video)
        return str(path)

    def save_exports(self, job_id: str, exports: dict[str, bytes]) -> dict[str, str]:
        """Save SNS-ready exports. Returns {name: path} map."""
        d = self._job_dir(job_id, "sns")
        paths = {}
        for name, data in exports.items():
            path = d / name
            path.write_bytes(data)
            paths[name] = str(path)
        return paths
