import json
import os
import uuid

import inotify.adapters
import redis

WATCH_DIR = "/srv/lookbook/inbox"
QUEUE_KEY = "lookbook:queue:pending"
EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def load_config() -> dict:
    """Load watch folder default config."""
    path = "/srv/lookbook/watch_config.json"
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {
        "prompt": "professional fashion lookbook photo, studio lighting, clean background, high quality",
        "negative_prompt": "low quality, blurry, deformed, watermark, text",
        "workflow": "lookbook_portrait",
        "upscale": True,
        "make_reel": False,
        "platforms": ["instagram"],
        "params": {"steps": 25, "cfg": 7.0, "width": 1024, "height": 1024},
    }


def watch():
    """Watch inbox folder for new images and auto-enqueue jobs."""
    r = redis.Redis(host="localhost", port=6379, decode_responses=True)
    i = inotify.adapters.Inotify()

    os.makedirs(WATCH_DIR, exist_ok=True)
    i.add_watch(WATCH_DIR)

    print(f"Watching {WATCH_DIR} for new files...")
    config = load_config()

    for event in i.event_gen(yield_nones=False):
        (_, type_names, _, filename) = event

        if "IN_CLOSE_WRITE" not in type_names:
            continue

        ext = os.path.splitext(filename)[1].lower()
        if ext not in EXTENSIONS:
            continue

        filepath = os.path.join(WATCH_DIR, filename)
        print(f"New image detected: {filepath}")

        job = {
            "id": str(uuid.uuid4()),
            "source": "watch_folder",
            "source_file": filepath,
            "prompt": config.get("prompt", ""),
            "negative_prompt": config.get("negative_prompt", ""),
            "workflow": config.get("workflow", "lookbook_portrait"),
            "upscale": config.get("upscale", True),
            "face_fix": config.get("face_fix", False),
            "make_reel": config.get("make_reel", False),
            "reel_style": config.get("reel_style", "zoom_pan"),
            "platforms": config.get("platforms", ["instagram"]),
            "params": config.get("params", {}),
        }

        r.lpush(QUEUE_KEY, json.dumps(job))
        print(f"Job {job['id'][:8]} enqueued for {filename}")


if __name__ == "__main__":
    watch()
