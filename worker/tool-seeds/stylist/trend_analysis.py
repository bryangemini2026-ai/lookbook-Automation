"""
Trend Analysis Tool — stylist agent.

Analyzes fashion trends and generates recommendations.
"""

import json
import os
from datetime import datetime

from modules.brain import BrainModule


TOOL_NAME = "trend_analysis"
AGENT_ID = "stylist"


def run(keywords: list[str] = None, platforms: list[str] = None, days: int = 7) -> dict:
    """
    Run trend analysis.

    Returns:
        {
            "trending_hashtags": [...],
            "trending_styles": [...],
            "trending_colors": [...],
            "recommendations": "..."
        }
    """
    brain = BrainModule()
    recent_trends = brain.get_recent_trends(days)

    # Aggregate trends from brain
    all_hashtags = set()
    all_styles = set()
    all_colors = set()

    for day in recent_trends:
        all_hashtags.update(day.get("hashtags", []))
        all_styles.update(day.get("styles", []))
        all_colors.update(day.get("colors", []))

    # If no brain data, use defaults
    if not recent_trends:
        all_hashtags = {"#fashion", "#ootd", "#lookbook", "#styleinspo"}
        all_styles = {"minimalist", "streetwear", "y2k"}
        all_colors = {"beige", "olive", "navy"}

    recommendations = generate_recommendations(all_styles, all_colors)

    return {
        "trending_hashtags": list(all_hashtags)[:20],
        "trending_styles": list(all_styles),
        "trending_colors": list(all_colors),
        "recommendations": recommendations,
    }


def generate_recommendations(styles: set, colors: set) -> str:
    """Generate style recommendations from trends."""
    style_str = ", ".join(list(styles)[:5])
    color_str = ", ".join(list(colors)[:5])
    return (
        f"현재 인기 스타일: {style_str}\n"
        f"인기 컬러: {color_str}\n"
        f"추천: 미니멀리즘 배경 + 대비 강한 컬러 조합으로 시선을 끄는 룩북을 제작하세요."
    )
