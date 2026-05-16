"""
Lookbook Generate Tool — photographer agent.

Optimizes prompts and triggers ComfyUI generation.
"""

from agents import get_persona_prompt
from modules.brain import BrainModule


TOOL_NAME = "lookbook_generate"
AGENT_ID = "photographer"


def run(prompt: str, workflow: str = "lookbook_portrait", params: dict = None,
        count: int = 1, reference_style: str = None) -> dict:
    """
    Generate lookbook images with prompt optimization.

    Returns:
        {"optimized_prompt": "...", "negative_prompt": "...", "workflow": "...", "params": {...}}
    """
    brain = BrainModule()
    brand = brain.get_brand_guidelines()

    # Optimize prompt based on brand guidelines and trends
    optimized = optimize_prompt(prompt, brand, reference_style)

    default_params = {
        "steps": 25,
        "cfg": 7.0,
        "width": 1024,
        "height": 1024,
        "seed": -1,
    }
    if params:
        default_params.update(params)

    return {
        "optimized_prompt": optimized["positive"],
        "negative_prompt": optimized["negative"],
        "workflow": workflow,
        "params": default_params,
        "count": count,
    }


def optimize_prompt(prompt: str, brand: str = "", style: str = None) -> dict:
    """Optimize prompt with brand context and photography best practices."""
    base_positive = (
        f"{prompt}, professional fashion photography, studio lighting, "
        f"clean background, high quality, sharp focus, editorial style"
    )

    if style:
        base_positive += f", {style} aesthetic"

    base_negative = (
        "low quality, blurry, deformed, watermark, text, "
        "bad anatomy, extra limbs, disfigured, poorly drawn"
    )

    return {
        "positive": base_positive,
        "negative": base_negative,
    }
