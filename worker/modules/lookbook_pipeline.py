"""
Lookbook Pipeline Orchestrator.

전체 6단계 파이프라인을 순차 실행합니다.
각 단계마다 Telegram 승인을 받습니다.

STEP 1: 크롤링 → 상품 수집
STEP 2: 이미지 생성 → Telegram 승인
STEP 3: 영상 생성 → Telegram 승인
STEP 4: 편집 → Telegram 승인
STEP 5: 업로드 → 최종 승인
STEP 6: 분석 → 피드백

사용:
    pipeline = LookbookPipeline(redis_client)
    result = pipeline.run_full(product)
    # 또는
    result = pipeline.run_from_step(2, product)  # STEP 2부터 시작
"""

import uuid
import json
from datetime import datetime

import redis

from modules.pipeline_steps.step1_crawl import Step1Crawl
from modules.pipeline_steps.step2_image import Step2ImageGen
from modules.pipeline_steps.step3_video import Step3VideoGen
from modules.pipeline_steps.step4_edit import Step4Edit
from modules.pipeline_steps.step5_upload import Step5Upload
from modules.pipeline_steps.step6_analytics import Step6Analytics
from modules.telegram_approval import TelegramApproval


class LookbookPipeline:
    """
    6단계 룩북 파이프라인 오케스트레이터.

    각 단계는 독립적으로 실행되며, Telegram 승인 후 다음 단계로 진행합니다.
    """

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.approval = TelegramApproval()

        # 파이프라인 단계 초기화
        self.step1 = Step1Crawl()
        self.step2 = Step2ImageGen(redis_client)
        self.step3 = Step3VideoGen(redis_client)
        self.step4 = Step4Edit(redis_client)
        self.step5 = Step5Upload(redis_client)
        self.step6 = Step6Analytics()

    def run_full(self, product: dict = None) -> dict:
        """
        전체 파이프라인 실행 (STEP 1~6).

        Args:
            product: 수동으로 지정한 상품. None이면 STEP 1에서 자동 수집.

        Returns:
            전체 파이프라인 결과
        """
        job_id = str(uuid.uuid4())
        results = {"job_id": job_id, "steps": {}, "started_at": datetime.utcnow().isoformat()}

        print(f"[Pipeline] 전체 파이프라인 시작 (job: {job_id[:8]})")

        # STEP 1: 크롤링
        if product is None:
            print(f"[Pipeline] === STEP 1: 크롤링 ===")
            step1_result = self.step1.execute()
            results["steps"]["step1"] = step1_result

            if not step1_result.get("recommendations"):
                print(f"[Pipeline] 추천 상품 없음, 중단")
                return results

            product = step1_result["recommendations"][0]
            print(f"[Pipeline] 추천 상품: {product.get('name')}")

        # STEP 2: 이미지 생성
        print(f"[Pipeline] === STEP 2: 이미지 생성 ===")
        self.approval.notify_step("Pipeline", f"STEP 2 시작: {product.get('name', 'N/A')}")
        step2_result = self.step2.execute(product, job_id)
        results["steps"]["step2"] = step2_result

        if step2_result["status"] != "approved":
            print(f"[Pipeline] STEP 2 미승인, 중단")
            return results

        # STEP 3: 영상 생성
        print(f"[Pipeline] === STEP 3: 영상 생성 ===")
        self.approval.notify_step("Pipeline", "STEP 3 시작: 영상 생성")
        step3_result = self.step3.execute(
            step2_result["images"], job_id, product
        )
        results["steps"]["step3"] = step3_result

        if step3_result["status"] != "approved":
            print(f"[Pipeline] STEP 3 미승인, 중단")
            return results

        # STEP 4: 편집
        print(f"[Pipeline] === STEP 4: 편집 ===")
        self.approval.notify_step("Pipeline", "STEP 4 시작: 편집")
        step4_result = self.step4.execute(
            step3_result["video_path"], job_id, product
        )
        results["steps"]["step4"] = step4_result

        if step4_result["status"] != "approved":
            print(f"[Pipeline] STEP 4 미승인, 중단")
            return results

        # STEP 5: 업로드
        print(f"[Pipeline] === STEP 5: 업로드 ===")
        self.approval.notify_step("Pipeline", "STEP 5 시작: YouTube 업로드")
        step5_result = self.step5.execute(
            step4_result["videos"], job_id, product
        )
        results["steps"]["step5"] = step5_result

        if step5_result["status"] != "published":
            print(f"[Pipeline] STEP 5 미승인, 중단")
            return results

        # STEP 6: 분석
        print(f"[Pipeline] === STEP 6: 분석 ===")
        video_id = step5_result.get("draft", {}).get("video_id", "")
        step6_result = self.step6.execute(video_id, product, job_id)
        results["steps"]["step6"] = step6_result

        results["completed_at"] = datetime.utcnow().isoformat()
        results["status"] = "completed"

        print(f"[Pipeline] 전체 파이프라인 완료!")
        self.approval.notify_step("Pipeline", f"✅ 전체 파이프라인 완료! Job: {job_id[:8]}")

        return results

    def run_from_step(self, step: int, product: dict, job_id: str = None) -> dict:
        """
        특정 단계부터 파이프라인 실행.

        Args:
            step: 시작 단계 (2~6)
            product: 상품 정보
            job_id: 기존 작업 ID (None이면 새로 생성)
        """
        if job_id is None:
            job_id = str(uuid.uuid4())

        results = {"job_id": job_id, "steps": {}, "started_at": datetime.utcnow().isoformat()}

        if step <= 2:
            step2_result = self.step2.execute(product, job_id)
            results["steps"]["step2"] = step2_result
            if step2_result["status"] != "approved":
                return results
            approved_images = step2_result["images"]
        else:
            approved_images = []

        if step <= 3 and approved_images:
            step3_result = self.step3.execute(approved_images, job_id, product)
            results["steps"]["step3"] = step3_result
            if step3_result["status"] != "approved":
                return results
            video_path = step3_result["video_path"]
        else:
            video_path = None

        if step <= 4 and video_path:
            step4_result = self.step4.execute(video_path, job_id, product)
            results["steps"]["step4"] = step4_result
            if step4_result["status"] != "approved":
                return results
            videos = step4_result["videos"]
        else:
            videos = {}

        if step <= 5 and videos:
            step5_result = self.step5.execute(videos, job_id, product)
            results["steps"]["step5"] = step5_result

        results["completed_at"] = datetime.utcnow().isoformat()
        return results
