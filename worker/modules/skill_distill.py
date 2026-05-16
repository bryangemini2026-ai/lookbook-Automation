"""
Skill Distillation System.

Automatically extracts reusable patterns from successful outputs.
Inspired by Connect AI's skill-distill.md pattern.

When a job succeeds with high engagement or user approval:
1. Extract the key patterns (prompt structure, style, parameters)
2. Save as a reusable skill document in brain/10_Wiki/styles/
3. Reference in future generation tasks
"""

import json
import os
from datetime import datetime

from modules.brain import BrainModule


class SkillDistillModule:
    """
    Extracts and stores reusable patterns from successful content.
    """

    def __init__(self):
        self.brain = BrainModule()

    def distill_from_job(self, job: dict, results: dict, performance: dict = None):
        """
        Analyze a completed job and extract reusable patterns.

        Args:
            job: Original job data (prompt, workflow, params)
            results: Generation results (images, video, exports)
            performance: Optional SNS performance metrics (likes, views, ctr)
        """
        patterns = []

        # ── Pattern 1: Prompt Structure ──
        prompt_pattern = self._extract_prompt_pattern(job)
        if prompt_pattern:
            patterns.append(prompt_pattern)

        # ── Pattern 2: Style Pattern ──
        style_pattern = self._extract_style_pattern(job, results)
        if style_pattern:
            patterns.append(style_pattern)

        # ── Pattern 3: Parameter Pattern ──
        param_pattern = self._extract_param_pattern(job, results)
        if param_pattern:
            patterns.append(param_pattern)

        # ── Pattern 4: Performance Pattern ──
        if performance:
            perf_pattern = self._extract_performance_pattern(job, performance)
            if perf_pattern:
                patterns.append(perf_pattern)

        # Save patterns as skills
        for pattern in patterns:
            self._save_skill(pattern)

        return patterns

    def _extract_prompt_pattern(self, job: dict) -> dict | None:
        """Extract reusable prompt structure."""
        prompt = job.get("prompt", "")
        if not prompt or len(prompt) < 20:
            return None

        # Identify prompt components
        components = {
            "subject": self._extract_subject(prompt),
            "style": self._extract_style_keywords(prompt),
            "lighting": self._extract_lighting(prompt),
            "mood": self._extract_mood(prompt),
        }

        # Only save if has meaningful structure
        if any(components.values()):
            return {
                "type": "prompt_structure",
                "name": f"prompt_{job.get('workflow', 'default')}_{datetime.utcnow().strftime('%Y%m%d')}",
                "pattern": f"Prompt structure: {json.dumps(components, ensure_ascii=False)}",
                "example": prompt,
                "workflow": job.get("workflow", ""),
            }
        return None

    def _extract_style_pattern(self, job: dict, results: dict) -> dict | None:
        """Extract style patterns from successful generation."""
        workflow = job.get("workflow", "")
        params = job.get("params", {})

        if not workflow:
            return None

        style_desc = f"Workflow: {workflow}"
        if params:
            style_desc += f", Steps: {params.get('steps', '?')}, CFG: {params.get('cfg', '?')}"
            style_desc += f", Resolution: {params.get('width', '?')}x{params.get('height', '?')}"

        return {
            "type": "style",
            "name": f"style_{workflow}_{datetime.utcnow().strftime('%Y%m%d')}",
            "pattern": style_desc,
            "example": job.get("prompt", "")[:100],
            "workflow": workflow,
            "params": params,
        }

    def _extract_param_pattern(self, job: dict, results: dict) -> dict | None:
        """Extract parameter patterns from successful generation."""
        params = job.get("params", {})
        if not params:
            return None

        # Check if specific parameters led to good results
        steps = params.get("steps", 25)
        cfg = params.get("cfg", 7.0)

        if steps >= 30 or cfg >= 8.0:
            return {
                "type": "params",
                "name": f"params_{datetime.utcnow().strftime('%Y%m%d')}",
                "pattern": f"High-quality settings: steps={steps}, cfg={cfg}",
                "example": json.dumps(params),
                "params": params,
            }
        return None

    def _extract_performance_pattern(self, job: dict, performance: dict) -> dict | None:
        """Extract patterns from high-performing content."""
        ctr = performance.get("ctr", 0)
        likes = performance.get("likes", 0)
        views = performance.get("views", 0)

        # Only distill if above average
        if ctr < 3.0 and likes < 100:
            return None

        return {
            "type": "performance",
            "name": f"high_perform_{datetime.utcnow().strftime('%Y%m%d')}",
            "pattern": f"High engagement: CTR={ctr}%, Likes={likes}, Views={views}",
            "example": job.get("prompt", "")[:100],
            "metrics": performance,
        }

    def _save_skill(self, pattern: dict):
        """Save a distilled skill to the brain."""
        name = pattern["name"]
        pattern_text = pattern["pattern"]
        examples = [pattern.get("example", "")]

        self.brain.distill_skill(name, pattern_text, examples)
        print(f"[SkillDistill] Distilled: {name}")

    # ── Prompt Analysis Helpers ──

    def _extract_subject(self, prompt: str) -> str:
        """Extract subject from prompt."""
        subjects = ["model", "woman", "man", "outfit", "dress", "lookbook", "fashion"]
        for s in subjects:
            if s in prompt.lower():
                return s
        return ""

    def _extract_style_keywords(self, prompt: str) -> str:
        """Extract style keywords from prompt."""
        styles = ["minimalist", "editorial", "streetwear", "luxury", "casual", "elegant",
                   "modern", "classic", "bohemian", "aesthetic", "professional"]
        found = [s for s in styles if s in prompt.lower()]
        return ", ".join(found) if found else ""

    def _extract_lighting(self, prompt: str) -> str:
        """Extract lighting description from prompt."""
        lighting = ["studio lighting", "natural light", "soft light", "dramatic lighting",
                     "warm lighting", "cool lighting", "golden hour", "backlit"]
        for l in lighting:
            if l in prompt.lower():
                return l
        return ""

    def _extract_mood(self, prompt: str) -> str:
        """Extract mood from prompt."""
        moods = ["elegant", "edgy", "soft", "bold", "calm", "dynamic", "moody", "bright"]
        found = [m for m in moods if m in prompt.lower()]
        return ", ".join(found) if found else ""

    # ── Skill Retrieval ──

    def get_relevant_skills(self, workflow: str = None, style: str = None) -> list[dict]:
        """Get skills relevant to the current task."""
        guides = self.brain.get_style_guides()
        relevant = []

        for name, content in guides.items():
            # Match by workflow or style keywords
            if workflow and workflow in name:
                relevant.append({"name": name, "content": content})
            elif style and style in content.lower():
                relevant.append({"name": name, "content": content})

        return relevant

    def get_skill_summary(self) -> str:
        """Get a summary of all distilled skills."""
        guides = self.brain.get_style_guides()
        if not guides:
            return "아직 추출된 스킬이 없습니다."

        lines = [f"*Distilled Skills ({len(guides)} total)*", ""]
        for name, content in list(guides.items())[:10]:
            # Extract first line as summary
            first_line = content.split("\n")[0] if content else ""
            lines.append(f"- {name}: {first_line[:60]}")

        return "\n".join(lines)
