"""
Engagement Report Tool — analyst agent.

Analyzes SNS performance metrics.
"""

from modules.brain import BrainModule


TOOL_NAME = "engagement_report"
AGENT_ID = "analyst"


def run(platform: str = "instagram", period: str = "7d", job_id: str = None) -> dict:
    """
    Generate engagement report.

    Returns:
        {
            "platform": "...",
            "period": "...",
            "metrics": {"likes": 0, "views": 0, ...},
            "comparison": {"vs_average": "...", "vs_previous": "..."},
            "recommendations": "..."
        }
    """
    brain = BrainModule()

    # TODO: Connect to actual SNS APIs for real metrics
    metrics = {
        "total_posts": 0,
        "total_likes": 0,
        "total_views": 0,
        "total_comments": 0,
        "avg_engagement_rate": 0.0,
        "top_post": None,
    }

    comparison = {
        "vs_average": "데이터 수집 중",
        "vs_previous": "데이터 수집 중",
    }

    recommendations = generate_recommendations(metrics)

    return {
        "platform": platform,
        "period": period,
        "metrics": metrics,
        "comparison": comparison,
        "recommendations": recommendations,
    }


def generate_recommendations(metrics: dict) -> str:
    """Generate recommendations from metrics."""
    if metrics["total_posts"] == 0:
        return "아직 포스팅 데이터가 없습니다. SNS에 콘텐츠를 올려보세요!"
    return "분석 결과를 바탕으로 최적 포스팅 시간과 해시태그를 조정하세요."
