"""
Crawling Agent — 무신사/쿠팡 인기 의류 자동 수집.

수집 데이터:
- 인기 TOP 의류 (실시간 랭킹)
- 시즌 신상품
- 상품 이미지 + 정보 + 가격
- 어필리에이트 링크

저장:
- Brain 시스템에 일별 데이터 축적
- 이미지는 로컬 스토리지에 저장
"""

import json
import os
import re
from datetime import datetime
from dataclasses import dataclass, asdict

import httpx

from config import settings
from modules.brain import BrainModule


@dataclass
class Product:
    """수집된 상품 정보."""
    platform: str          # "musinsa" | "coupang"
    product_id: str
    name: str
    brand: str
    price: int
    original_price: int
    discount_rate: int
    category: str          # "상의" | "하의" | "아우터" | "원피스" | "신발"
    image_url: str
    product_url: str
    affiliate_url: str     # 어필리에이트 변환 URL
    ranking: int           # 랭킹 순위
    review_count: int
    rating: float
    tags: list[str]
    season: str            # "spring" | "summer" | "fall" | "winter"
    collected_at: str      # ISO timestamp


class CrawlingAgent:
    """
    무신사/쿠팡 의류 크롤링 에이전트.
    매일 인기 상품과 시즌 상품을 수집합니다.
    """

    CATEGORIES = ["상의", "하의", "아우터", "원피스", "신발"]
    SEASONS = {
        (3, 4, 5): "spring",
        (6, 7, 8): "summer",
        (9, 10, 11): "fall",
        (12, 1, 2): "winter",
    }

    def __init__(self):
        self.brain = BrainModule()
        self.today = datetime.utcnow().strftime("%Y-%m-%d")
        self.current_season = self._get_season()

    def _get_season(self) -> str:
        month = datetime.utcnow().month
        for months, season in self.SEASONS.items():
            if month in months:
                return season
        return "spring"

    def crawl_musinsa_trending(self, category: str = "상의", limit: int = 20) -> list[Product]:
        """
        무신사 인기 상품 크롤링.

        참고: 실제 크롤링은 웹 스크래핑 또는 API 사용.
        현재는 목업 데이터로 구조를 잡고, 향후 실제 크롤러로 교체.
        """
        print(f"[Crawler] 무신사 인기 상품 수집: {category} (시즌: {self.current_season})")

        # TODO: 실제 무신사 크롤링 구현
        # 1. https://www.musinsa.com/ranking/best 에서 HTML 파싱
        # 2. 상품 이미지, 정보, 가격 추출
        # 3. 어필리에이트 링크 변환

        products = self._mock_musinsa_products(category, limit)

        # Brain에 저장
        self._save_to_brain("musinsa", category, products)

        return products

    def crawl_coupang_trending(self, category: str = "의류", limit: int = 20) -> list[Product]:
        """
        쿠팡 인기 상품 크롤링.

        참고: 쿠팡은 robots.txt 제한이 엄격함.
        쿠팡 파트너스 API를 우선 사용 권장.
        """
        print(f"[Crawler] 쿠팡 인기 상품 수집: {category}")

        # TODO: 쿠팡 파트너스 API 연동
        # 1. Coupang Partners API로 상품 검색
        # 2. 어필리에이트 링크 자동 생성
        # 3. 상품 이미지 + 정보 저장

        products = self._mock_coupang_products(category, limit)

        self._save_to_brain("coupang", category, products)

        return products

    def crawl_seasonal(self, limit: int = 30) -> list[Product]:
        """
        시즌 추천 상품 수집.
        현재 시즌에 맞는 인기 상품을 플랫폼에서 수집합니다.
        """
        print(f"[Crawler] 시즌 상품 수집: {self.current_season}")

        all_products = []

        for category in self.CATEGORIES:
            musinsa = self.crawl_musinsa_trending(category, limit=5)
            all_products.extend(musinsa)

        # 시즌별 추천 이유 생성
        for product in all_products:
            product.tags.append(self.current_season)
            product.season = self.current_season

        return all_products

    def collect_daily(self) -> dict:
        """
        매일 실행되는 수집 작업.
        인기 상품 + 시즌 상품을 모두 수집합니다.
        """
        print(f"[Crawler] === 일일 수집 시작 ({self.today}) ===")

        results = {
            "date": self.today,
            "season": self.current_season,
            "musinsa": {},
            "coupang": {},
            "total": 0,
        }

        # 무신사 인기 TOP
        for category in self.CATEGORIES:
            products = self.crawl_musinsa_trending(category, limit=10)
            results["musinsa"][category] = [asdict(p) for p in products]
            results["total"] += len(products)

        # 쿠팡 인기 TOP
        for category in self.CATEGORIES:
            products = self.crawl_coupang_trending(category, limit=10)
            results["coupang"][category] = [asdict(p) for p in products]
            results["total"] += len(products)

        # 일별 리포트 저장
        report_path = os.path.join(
            settings.STORAGE_BASE, "brain", "00_Raw", self.today, "crawl_report.json"
        )
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, "w") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"[Crawler] 수집 완료: {results['total']}개 상품")
        return results

    def get_recommendations(self, count: int = 5) -> list[dict]:
        """
        오늘의 추천 상품 선정.
        랭킹, 리뷰, 할인율을 기반으로 Top N을 선정합니다.
        """
        report_path = os.path.join(
            settings.STORAGE_BASE, "brain", "00_Raw", self.today, "crawl_report.json"
        )

        if not os.path.exists(report_path):
            return []

        with open(report_path) as f:
            data = json.load(f)

        all_products = []
        for platform_data in data.get("musinsa", {}).values():
            all_products.extend(platform_data)
        for platform_data in data.get("coupang", {}).values():
            all_products.extend(platform_data)

        # 점수 계산: 랭킹 + 리뷰 + 할인율
        scored = []
        for p in all_products:
            score = (
                (100 - min(p.get("ranking", 100), 100)) * 0.4  # 랭킹 (높을수록 좋음)
                + min(p.get("review_count", 0), 1000) * 0.0003  # 리뷰 수
                + p.get("discount_rate", 0) * 0.3  # 할인율
            )
            scored.append({**p, "score": score, "recommendation_reason": self._generate_reason(p)})

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:count]

    def _generate_reason(self, product: dict) -> str:
        """추천 이유 생성."""
        reasons = []

        if product.get("ranking", 999) <= 10:
            reasons.append(f"{product['platform']} 랭킹 {product['ranking']}위")

        if product.get("review_count", 0) >= 100:
            reasons.append(f"리뷰 {product['review_count']}개")

        if product.get("discount_rate", 0) >= 30:
            reasons.append(f"{product['discount_rate']}% 할인 중")

        if product.get("rating", 0) >= 4.5:
            reasons.append(f"평점 {product['rating']}")

        season = product.get("season", "")
        if season:
            season_names = {"spring": "봄", "summer": "여름", "fall": "가을", "winter": "겨울"}
            reasons.append(f"{season_names.get(season, season)} 시즌 추천")

        return " · ".join(reasons) if reasons else "인기 상품"

    def _save_to_brain(self, platform: str, category: str, products: list[Product]):
        """수집 데이터를 Brain에 저장."""
        day_dir = os.path.join(settings.STORAGE_BASE, "brain", "00_Raw", self.today)
        os.makedirs(day_dir, exist_ok=True)

        path = os.path.join(day_dir, f"{platform}_{category}.json")
        with open(path, "w") as f:
            json.dump([asdict(p) for p in products], f, indent=2, ensure_ascii=False)

    # ── 목업 데이터 (실제 크롤러 구현 전까지 사용) ──

    def _mock_musinsa_products(self, category: str, limit: int) -> list[Product]:
        """목업 무신사 상품 데이터."""
        products = []
        for i in range(min(limit, 5)):
            products.append(Product(
                platform="musinsa",
                product_id=f"MU{self.today.replace('-','')}{i:03d}",
                name=f"[무신사] {category} 인기 상품 {i+1}",
                brand=f"브랜드{chr(65+i)}",
                price=29900 + i * 10000,
                original_price=49900 + i * 10000,
                discount_rate=30 + i * 5,
                category=category,
                image_url=f"https://via.placeholder.com/400x500?text={category}+{i+1}",
                product_url=f"https://www.musinsa.com/products/mock{i+1}",
                affiliate_url=f"https://www.musinsa.com/products/mock{i+1}?ref=lookbook_ai",
                ranking=i + 1,
                review_count=500 - i * 80,
                rating=4.8 - i * 0.1,
                tags=[category, self.current_season, "인기"],
                season=self.current_season,
                collected_at=datetime.utcnow().isoformat(),
            ))
        return products

    def _mock_coupang_products(self, category: str, limit: int) -> list[Product]:
        """목업 쿠팡 상품 데이터."""
        products = []
        for i in range(min(limit, 5)):
            products.append(Product(
                platform="coupang",
                product_id=f"CP{self.today.replace('-','')}{i:03d}",
                name=f"[쿠팡] {category} 로켓배송 상품 {i+1}",
                brand=f"쿠팡브랜드{chr(65+i)}",
                price=19900 + i * 8000,
                original_price=39900 + i * 8000,
                discount_rate=40 + i * 3,
                category=category,
                image_url=f"https://via.placeholder.com/400x500?text=Coupang+{category}+{i+1}",
                product_url=f"https://www.coupang.com/products/mock{i+1}",
                affiliate_url=f"https://www.coupang.com/products/mock{i+1}?ref=lookbook_ai",
                ranking=i + 1,
                review_count=1000 - i * 150,
                rating=4.7 - i * 0.1,
                tags=[category, self.current_season, "로켓배송"],
                season=self.current_season,
                collected_at=datetime.utcnow().isoformat(),
            ))
        return products
