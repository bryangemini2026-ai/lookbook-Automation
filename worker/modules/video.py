import subprocess
import tempfile
import os

from clients.comfyui import ComfyUIClient


# Platform video specifications
PLATFORM_SPECS = {
    "instagram": {"width": 1080, "height": 1350, "max_duration": 90},
    "reels":     {"width": 1080, "height": 1920, "max_duration": 90},
    "tiktok":    {"width": 1080, "height": 1920, "max_duration": 60},
    "twitter":   {"width": 1200, "height": 675,  "max_duration": 140},
}


class VideoModule:
    """Handles video/reel creation. FFmpeg-based (zero GPU) or AI-based (AnimateDiff)."""

    def __init__(self, comfyui_video: ComfyUIClient):
        self.comfyui = comfyui_video

    def ffmpeg_reel(self, images: list[bytes], style: str = "zoom_pan",
                    duration: float = 3.0, platform: str = "instagram") -> bytes:
        """
        Create a short reel from still images using FFmpeg.
        Zero GPU cost. Styles: zoom_pan, fade, slide.
        """
        spec = PLATFORM_SPECS.get(platform, PLATFORM_SPECS["instagram"])

        with tempfile.TemporaryDirectory() as tmpdir:
            # Save images to temp files
            for i, img_bytes in enumerate(images):
                path = os.path.join(tmpdir, f"input_{i:03d}.png")
                with open(path, "wb") as f:
                    f.write(img_bytes)

            output_path = os.path.join(tmpdir, "output.mp4")

            # Build FFmpeg filter based on style
            if style == "zoom_pan":
                filter_complex = self._build_zoom_pan_filter(len(images), spec, duration)
            elif style == "fade":
                filter_complex = self._build_fade_filter(len(images), spec, duration)
            else:
                filter_complex = self._build_zoom_pan_filter(len(images), spec, duration)

            # Run FFmpeg
            cmd = [
                "ffmpeg", "-y",
                *[arg for i in range(len(images)) for arg in ["-i", os.path.join(tmpdir, f"input_{i:03d}.png")]],
                "-filter_complex", filter_complex,
                "-map", "[outv]",
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "18",
                "-pix_fmt", "yuv420p",
                "-r", "30",
                output_path,
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg failed: {result.stderr}")

            with open(output_path, "rb") as f:
                return f.read()

    def _build_zoom_pan_filter(self, count: int, spec: dict, dur: float) -> str:
        """Ken Burns: slow zoom + pan across each image."""
        filters = []
        frames = int(dur * 30)
        for i in range(count):
            filters.append(
                f"[{i}:v]scale=8000:-1,"
                f"zoompan=z='min(zoom+0.0015,1.3)'"
                f":x='iw/2-(iw/zoom/2)+((iw/zoom)*on/{frames})'"
                f":y='ih/2-(ih/zoom/2)'"
                f":d={frames}:s={spec['width']}x{spec['height']}:fps=30"
                f"[v{i}]"
            )

        concat = "".join(f"[v{i}]" for i in range(count))
        filters.append(f"{concat}concat=n={count}:v=1:a=0[outv]")
        return ";".join(filters)

    def _build_fade_filter(self, count: int, spec: dict, dur: float) -> str:
        """Crossfade between images."""
        # Simplified fade — can be expanded
        filters = []
        frames = int(dur * 30)
        for i in range(count):
            filters.append(
                f"[{i}:v]scale={spec['width']}:{spec['height']}:force_original_aspect_ratio=decrease,"
                f"pad={spec['width']}:{spec['height']}:(ow-iw)/2:(oh-ih)/2,"
                f"setsar=1,format=yuv420p,"
                f"fade=t=in:st=0:d=0.5,fade=t=out:st={dur - 0.5}:d=0.5[v{i}]"
            )

        concat = "".join(f"[v{i}]" for i in range(count))
        filters.append(f"{concat}concat=n={count}:v=1:a=0[outv]")
        return ";".join(filters)

    def ai_generate(self, image_bytes: bytes, motion_prompt: str = "") -> bytes:
        """
        AI-based video generation via ComfyUI Video server (AnimateDiff).
        This is a placeholder — actual implementation needs video workflow template.
        """
        print("  AI Video: placeholder (AnimateDiff workflow not yet configured)")
        # TODO: Load video workflow, inject image, execute via self.comfyui
        return image_bytes
