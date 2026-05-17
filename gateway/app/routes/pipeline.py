"""
Lookbook Pipeline API routes.

전체 6단계 파이프라인 실행/관리.
"""

import json
import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import redis

from app.config import settings

router = APIRouter()
r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)

# Pipeline queue
PIPELINE_QUEUE = "lookbook:pipeline:pending"


class PipelineRequest(BaseModel):
    """파이프라인 실행 요청."""
    product: Optional[dict] = None  # 수동 상품 지정
    start_step: int = 2  # 시작 단계 (기본: 이미지 생성부터)
    max_retries: int = 3


class CrawlRequest(BaseModel):
    """크롤링 요청."""
    category: str = "상의"
    limit: int = 10


@router.post("/run")
def run_pipeline(req: PipelineRequest):
    """
    룩북 파이프라인 실행.

    product가 지정되면 해당 상품으로, 없으면 자동 크롤링 후 실행.
    start_step로 시작 단계를 지정할 수 있습니다.
    """
    job_id = str(uuid.uuid4())

    # Redis 큐에 등록
    job_data = {
        "id": job_id,
        "type": "lookbook_pipeline",
        "product": req.product,
        "start_step": req.start_step,
        "max_retries": req.max_retries,
    }
    r.lpush(PIPELINE_QUEUE, json.dumps(job_data))
    r.hset(f"job:{job_id}", mapping={
        "status": "pending",
        "type": "lookbook_pipeline",
        "start_step": str(req.start_step),
    })

    return {
        "job_id": job_id,
        "status": "pending",
        "message": f"파이프라인이 큐에 등록되었습니다. (STEP {req.start_step}부터)",
    }


@router.post("/crawl")
def run_crawl(req: CrawlRequest):
    """
    크롤링 에이전트 실행.

    무신사/쿠팡 인기 상품을 수집합니다.
    """
    job_id = str(uuid.uuid4())

    job_data = {
        "id": job_id,
        "type": "crawl",
        "category": req.category,
        "limit": req.limit,
    }
    r.lpush("lookbook:crawl:pending", json.dumps(job_data))

    return {
        "job_id": job_id,
        "status": "pending",
        "message": f"크롤링이 시작됩니다. (카테고리: {req.category})",
    }


@router.get("/status/{job_id}")
def get_pipeline_status(job_id: str):
    """파이프라인 작업 상태 조회."""
    data = r.hgetall(f"job:{job_id}")
    if not data:
        raise HTTPException(status_code=404, detail="Job not found")
    return data


@router.post("/approve/{job_id}")
def approve_step(job_id: str):
    """특정 단계 승인 (API에서 직접 승인 가능)."""
    r.hset(f"approval:{job_id}", "result", "approve")
    return {"job_id": job_id, "action": "approved"}


@router.post("/retry/{job_id}")
def retry_step(job_id: str):
    """특정 단계 재시도."""
    r.hset(f"approval:{job_id}", "result", "retry")
    return {"job_id": job_id, "action": "retry"}


@router.post("/edit/{job_id}")
def edit_step(job_id: str, edit_text: str = ""):
    """수정요청."""
    r.hset(f"approval:{job_id}", mapping={"result": "edit", "edit_text": edit_text})
    return {"job_id": job_id, "action": "edit", "edit_text": edit_text}
