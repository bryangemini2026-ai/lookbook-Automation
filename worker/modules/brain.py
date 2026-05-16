"""
Brain Knowledge System.

Accumulates trend data, campaign results, and brand knowledge over time.
Inspired by Connect AI's .secondbrain/ pattern.

Structure:
    /srv/lookbook/brain/
    ├── 00_Raw/          ← Daily trend data (auto-collected)
    ├── 10_Wiki/         ← Structured knowledge
    │   ├── styles/      ← Style guides
    │   ├── campaigns/   ← Campaign results
    │   └── brand.md     ← Brand guidelines
    └── _shared/
        ├── identity.md  ← Brand identity
        └── decisions.md ← Decision log
"""

import json
import os
from datetime import datetime

from config import settings


BRAIN_BASE = os.path.join(settings.STORAGE_BASE, "brain")

# Directory structure
DIRS = {
    "raw": os.path.join(BRAIN_BASE, "00_Raw"),
    "wiki": os.path.join(BRAIN_BASE, "10_Wiki"),
    "styles": os.path.join(BRAIN_BASE, "10_Wiki", "styles"),
    "campaigns": os.path.join(BRAIN_BASE, "10_Wiki", "campaigns"),
    "shared": os.path.join(BRAIN_BASE, "_shared"),
}


class BrainModule:
    """
    Knowledge accumulation system.
    Stores daily data, structures it over time, and makes it available
    for future content generation.
    """

    def __init__(self):
        self._ensure_dirs()

    def _ensure_dirs(self):
        for d in DIRS.values():
            os.makedirs(d, exist_ok=True)

    # ── Daily Trend Collection ──

    def collect_daily_trends(self):
        """Collect and store today's trend data."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        day_dir = os.path.join(DIRS["raw"], today)
        os.makedirs(day_dir, exist_ok=True)

        # Collect trending hashtags (placeholder — future: SNS API)
        trends = {
            "date": today,
            "hashtags": self._fetch_trending_hashtags(),
            "styles": self._fetch_trending_styles(),
            "colors": self._fetch_trending_colors(),
        }

        path = os.path.join(day_dir, "trends.json")
        with open(path, "w") as f:
            json.dump(trends, f, indent=2, ensure_ascii=False)

        print(f"[Brain] Trends saved: {path}")
        return trends

    def _fetch_trending_hashtags(self) -> list[str]:
        """Fetch trending fashion hashtags. Placeholder for API integration."""
        # TODO: Connect to Instagram/Twitter trending API
        return [
            "#fashion", "#ootd", "#lookbook", "#styleinspo",
            "#streetwear", "#minimalist", "#aesthetic", "#outfitoftheday",
        ]

    def _fetch_trending_styles(self) -> list[str]:
        """Fetch trending fashion styles. Placeholder."""
        return ["minimalist", "streetwear", "y2k", "old money", "quiet luxury"]

    def _fetch_trending_colors(self) -> list[str]:
        """Fetch trending colors. Placeholder."""
        return ["beige", "olive", "navy", "cream", "charcoal"]

    # ── Job Result Recording ──

    def record_job_result(self, job: dict, results: dict):
        """Record a completed job's results for future reference."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        day_dir = os.path.join(DIRS["raw"], today)
        os.makedirs(day_dir, exist_ok=True)

        record = {
            "job_id": job.get("id", ""),
            "timestamp": datetime.utcnow().isoformat(),
            "prompt": job.get("prompt", ""),
            "workflow": job.get("workflow", ""),
            "params": job.get("params", {}),
            "outputs": {
                "images": len(results.get("raw_images", [])),
                "reels": 1 if results.get("video") else 0,
                "exports": list(results.get("sns_exports", {}).keys()),
            },
        }

        # Append to daily log
        log_path = os.path.join(day_dir, "jobs.jsonl")
        with open(log_path, "a") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def record_performance(self, job_id: str, platform: str, metrics: dict):
        """Record SNS performance metrics for a posted content."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        day_dir = os.path.join(DIRS["raw"], today)
        os.makedirs(day_dir, exist_ok=True)

        record = {
            "job_id": job_id,
            "platform": platform,
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": metrics,  # likes, views, comments, shares, ctr
        }

        perf_path = os.path.join(day_dir, "performance.jsonl")
        with open(perf_path, "a") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    # ── Decision Log ──

    def log_decision(self, decision: str, context: str = ""):
        """Log a brand/content decision for future reference."""
        path = os.path.join(DIRS["shared"], "decisions.md")
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M")

        entry = f"\n## {now}\n{decision}\n"
        if context:
            entry += f"Context: {context}\n"

        with open(path, "a") as f:
            f.write(entry)

    # ── Skill Distillation ──

    def distill_skill(self, name: str, pattern: str, examples: list[str]):
        """
        Extract a reusable pattern from successful outputs.
        Called by the skill distillation system.
        """
        path = os.path.join(DIRS["styles"], f"{name}.md")
        content = f"""# {name}

## Pattern
{pattern}

## Examples
{chr(10).join(f'- {e}' for e in examples)}

## Auto-generated
Created: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}
"""
        with open(path, "w") as f:
            f.write(content)

        print(f"[Brain] Skill distilled: {name}")

    # ── Knowledge Retrieval ──

    def get_brand_guidelines(self) -> str:
        """Get brand guidelines for content generation."""
        path = os.path.join(DIRS["shared"], "identity.md")
        if os.path.exists(path):
            return open(path).read()
        return ""

    def get_style_guides(self) -> dict[str, str]:
        """Get all style guides."""
        guides = {}
        for f in os.listdir(DIRS["styles"]):
            if f.endswith(".md"):
                name = f[:-3]
                guides[name] = open(os.path.join(DIRS["styles"], f)).read()
        return guides

    def get_recent_trends(self, days: int = 7) -> list[dict]:
        """Get trend data from the last N days."""
        trends = []
        for i in range(days):
            date = datetime.utcnow().replace(hour=0, minute=0) - __import__('datetime').timedelta(days=i)
            path = os.path.join(DIRS["raw"], date.strftime("%Y-%m-%d"), "trends.json")
            if os.path.exists(path):
                with open(path) as f:
                    trends.append(json.load(f))
        return trends

    def get_decision_log(self) -> str:
        """Get all logged decisions."""
        path = os.path.join(DIRS["shared"], "decisions.md")
        if os.path.exists(path):
            return open(path).read()
        return ""

    # ── Brand Identity ──

    def set_brand_identity(self, identity: str):
        """Set or update brand identity."""
        path = os.path.join(DIRS["shared"], "identity.md")
        with open(path, "w") as f:
            f.write(identity)

    def initialize_defaults(self):
        """Initialize default brain files if they don't exist."""
        identity_path = os.path.join(DIRS["shared"], "identity.md")
        if not os.path.exists(identity_path):
            self.set_brand_identity("""# Brand Identity

## Name
(Your Brand Name)

## Style
fashion, lookbook, editorial

## Tone
professional, aspirational, clean

## Target Audience
fashion-conscious, 20-35, urban

## Visual Identity
- Colors: (your palette)
- Mood: (your mood)
- Photography: (your style)
""")

        decisions_path = os.path.join(DIRS["shared"], "decisions.md")
        if not os.path.exists(decisions_path):
            with open(decisions_path, "w") as f:
                f.write("# Decision Log\n\n")
                f.write("Track brand and content decisions here.\n\n")
