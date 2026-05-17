"""
STEP 1: 크롤링 에이전트

무신사/쿠팡 인기 의류 자동 수집.
매일 실행되며, 수집된 상품은 STEP 2의 입력으로 사용됩니다.
"""

from modules.crawler import CrawlingAgent


class Step1Crawl:
    """상품 크롤링 단계."""

    def __init__(self):
        self.crawler = CrawlingAgent()

    def execute(self) -> dict:
        """
        일일 크롤링 실행.

        Returns:
            {
                "date": "2026-05-17",
                "season": "spring",
                "recommendations": [...],  # 추천 상품 Top 5
                "total_crawled": 100,
            }
        """
        # 1. 전체 상품 수집
        report = self.crawler.collect_daily()

        # 2. 추천 상품 선정
        recommendations = self.crawler.get_recommendations(count=5)

        return {
            "date": report["date"],
            "season": report["season"],
            "recommendations": recommendations,
            "total_crawled": report["total"],
            "status": "completed",
        }
