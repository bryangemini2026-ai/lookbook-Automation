import json
import os

import redis

from config import settings
from clients.comfyui import ComfyUIClient
from clients.telegram import TelegramNotifier
from clients.storage import LocalStorage
from modules.gpu_manager import GPUManager
from modules.generation import GenerationModule
from modules.upscale import UpscaleModule
from modules.video import VideoModule
from modules.sns import SNSModule
from modules.brain import BrainModule
from modules.skill_distill import SkillDistillModule


class PipelineWorker:
    """
    Single-process pipeline executor.
    Reads jobs from Redis queue, executes sequentially.
    Each stage is a separate module for clean code,
    but they run in the same process — no distributed complexity.

    Integrates:
    - Brain: Knowledge accumulation
    - SkillDistill: Pattern extraction from successful outputs
    - Agent personas: Brand-consistent content
    """

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.gpu = GPUManager(redis_client)
        self.comfyui_image = ComfyUIClient(settings.COMFYUI_IMAGE_URL)
        self.comfyui_video = ComfyUIClient(settings.COMFYUI_VIDEO_URL)
        self.generation = GenerationModule(self.comfyui_image)
        self.upscale = UpscaleModule(self.comfyui_image)
        self.video = VideoModule(self.comfyui_video)
        self.sns = SNSModule(os.path.join(settings.STORAGE_BASE, "brand"))
        self.storage = LocalStorage(settings.STORAGE_BASE)
        self.telegram = TelegramNotifier()
        self.brain = BrainModule()
        self.skill_distill = SkillDistillModule()

    def execute(self, job: dict) -> dict:
        """Execute a full pipeline job."""
        job_id = job["id"]
        results = {}

        # ── Pre-flight: Get brand context from Brain ──
        brand_context = self.brain.get_brand_guidelines()
        relevant_skills = self.skill_distill.get_relevant_skills(
            workflow=job.get("workflow"),
        )

        # ── Stage 1: Image Generation ──
        self._update(job_id, "running", stage="generation")
        self.gpu.ensure_server("image")

        images = self.generation.generate(
            prompt=job["prompt"],
            negative=job.get("negative_prompt", ""),
            workflow=job.get("workflow", "lookbook_portrait"),
            params=job.get("params", {}),
        )
        results["raw_images"] = self.storage.save_images(job_id, "raw", images)
        print(f"  Saved {len(results['raw_images'])} raw images")

        # ── Stage 2: Upscale ──
        if job.get("upscale", False):
            self._update(job_id, "running", stage="upscale")
            upscaled = [self.upscale.upscale(img) for img in images]
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

            reel_type = job.get("reel_type", "ffmpeg")

            if reel_type == "ai_video":
                self.gpu.ensure_server("video")
                video = self.video.ai_generate(images[0], job.get("motion_prompt", ""))
            else:
                video = self.video.ffmpeg_reel(
                    images=images,
                    style=job.get("reel_style", "zoom_pan"),
                    duration=job.get("reel_duration", 3.0),
                    platform=job.get("platforms", ["instagram"])[0],
                )

            results["video"] = self.storage.save_video(job_id, "reel", video)
            print(f"  Saved video: {results['video']}")

        # ── Stage 6: SNS Export ──
        self._update(job_id, "running", stage="export")
        exports = self.sns.export_for_platforms(
            images=images,
            video_path=results.get("video"),
            platforms=job.get("platforms", ["instagram"]),
        )
        results["sns_exports"] = self.storage.save_exports(job_id, exports)
        print(f"  Exported {len(results['sns_exports'])} SNS assets")

        # ── Stage 7: Brain Recording ──
        self.brain.record_job_result(job, results)

        # ── Stage 8: Skill Distillation ──
        try:
            patterns = self.skill_distill.distill_from_job(job, results)
            if patterns:
                print(f"  Distilled {len(patterns)} skill patterns")
        except Exception as e:
            print(f"  Skill distill failed (non-fatal): {e}")

        # ── Stage 9: Notify ──
        self._update(job_id, "completed", results=results)
        self.telegram.notify_completion(job_id, results)

        return results

    def _update(self, job_id: str, status: str, **kwargs):
        """Update job status in Redis."""
        mapping = {"status": status}
        for k, v in kwargs.items():
            if isinstance(v, (dict, list)):
                mapping[k] = json.dumps(v)
            else:
                mapping[k] = str(v)
        self.redis.hset(f"job:{job_id}", mapping=mapping)
