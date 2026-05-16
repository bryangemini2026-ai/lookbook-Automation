"""
Instagram Post Tool — sns_manager agent.

Handles posting to Instagram with caption and hashtag optimization.
"""

from agents import get_persona_prompt


TOOL_NAME = "instagram_post"
AGENT_ID = "sns_manager"


def run(image_path: str, caption: str = "", hashtags: list[str] = None,
        schedule_time: str = None) -> dict:
    """
    Post to Instagram.

    Returns:
        {"status": "posted"|"scheduled", "post_id": "...", "url": "..."}
    """
    if not caption:
        caption = generate_caption(image_path)

    if not hashtags:
        hashtags = generate_hashtags(caption)

    # TODO: Instagram Graph API integration
    return {
        "status": "ready",
        "image_path": image_path,
        "caption": caption,
        "hashtags": hashtags,
        "schedule_time": schedule_time,
        "note": "Instagram API integration pending",
    }


def generate_caption(image_path: str) -> str:
    """Auto-generate caption for lookbook image."""
    return (
        "New lookbook drop ✨\n\n"
        "Clean lines, timeless style.\n"
        "Link in bio for full collection.\n\n"
        "#lookbook #fashion #ootd"
    )


def generate_hashtags(caption: str) -> list[str]:
    """Generate relevant hashtags."""
    base = [
        "#fashion", "#lookbook", "#ootd", "#styleinspo",
        "#streetwear", "#minimalist", "#aesthetic", "#outfitoftheday",
        "#fashionstyle", "#lookoftheday", "#whatiwore", "#stylegoals",
    ]
    return base
