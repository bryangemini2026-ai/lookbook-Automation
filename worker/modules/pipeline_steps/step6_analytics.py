"""
STEP 6: 분석 에이전트

조회수/댓글/좋아요 데이터 수집.
다음 의상 선정에 피드백 반영.
"""

from modules.brain import BrainModule


class Step6Analytics:
    """성과 분석 + 피드백 단계."""

    def __init__(self):
        self.brain = BrainModule()

    def execute(self, video_id: str, product: dict, job_id: str) -> dict:
        """
        성과 분석 실행.

        1. YouTube Analytics API로 데이터 수집
        2. Brain에 성과 기록
        3. 다음 의상 선정에 반영
        """
        print(f"[Step6] 성과 분석: {video_id}")

        # TODO: YouTube Analytics API 연동
        metrics = {
            "views": 0,
            "likes": 0,
            "comments": 0,
            "watch_time": 0,
            "ctr": 0.0,
        }

        # Brain에 기록
        self.brain.record_performance(
            job_id=job_id,
            platform="youtube",
            metrics=metrics,
        )

        return {
            "status": "completed",
            "metrics": metrics,
            "video_id": video_id,
        }
