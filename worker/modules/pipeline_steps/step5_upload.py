"""
STEP 5: 업로드 에이전트

YouTube 임시등록 + 제목/태그/설명 생성.
텔레그램으로 최종 내용 전송 → ✅최종승인 후에만 공개 배포.
"""

from modules.telegram_approval import TelegramApproval, ApprovalResult


class Step5Upload:
    """업로드 + 최종 승인 단계."""

    def __init__(self, redis_client):
        self.redis = redis_client
        self.approval = TelegramApproval()

    def execute(self, videos: dict, job_id: str,
                product: dict = None, max_retries: int = 3) -> dict:
        """
        업로드 + 최종 승인 루프.

        1. YouTube 임시등록 (unlisted)
        2. 제목/태그/설명 생성
        3. Telegram으로 최종 내용 전송
        4. ✅최종승인 후 공개(public) 전환
        """
        attempts = 0

        while attempts < max_retries:
            attempts += 1

            # 1. YouTube 임시등록
            print(f"[Step5] YouTube 임시등록 시도 {attempts}")
            draft = self._create_youtube_draft(videos, product)

            # 2. Telegram 최종 승인
            caption = self._build_caption(draft, product)
            result, edit_text = self.approval.request_approval(
                step="upload",
                job_id=job_id,
                caption=caption,
                timeout=1200,  # 20분 대기
            )

            if result == ApprovalResult.APPROVE:
                # 공개 전환
                self._publish(draft)
                return {"status": "published", "draft": draft, "attempts": attempts}
            elif result == ApprovalResult.RETRY:
                continue
            elif result == ApprovalResult.EDIT:
                draft = self._apply_edit(draft, edit_text)
                continue

        return {"status": "max_retries", "draft": None, "attempts": attempts}

    def _create_youtube_draft(self, videos: dict, product: dict) -> dict:
        """YouTube 임시등록."""
        # TODO: YouTube Data API 연동
        return {
            "title": f"룩북 AI - {product.get('name', 'Fashion Lookbook')}",
            "description": f"AI가 입어본 룩북 영상\n\n상품: {product.get('name', '')}\n브랜드: {product.get('brand', '')}",
            "tags": ["룩북", "패션", "AI", "lookbook", "fashion"],
            "status": "unlisted",
            "video_path": videos.get("youtube"),
        }

    def _publish(self, draft: dict):
        """YouTube 공개 전환."""
        # TODO: YouTube API로 public 전환
        print(f"[Step5] YouTube 공개: {draft.get('title')}")

    def _apply_edit(self, draft: dict, edit_text: str) -> dict:
        """수정요청 반영."""
        # TODO: NLP로 수정요청 해석
        return draft

    def _build_caption(self, draft, product):
        lines = [
            f"*📤 최종 업로드 확인*",
            f"",
            f"*제목:* {draft.get('title', 'N/A')}",
            f"*설명:* {draft.get('description', 'N/A')[:100]}...",
            f"*태그:* {', '.join(draft.get('tags', []))}",
            f"*상태:* 임시등록 (unlisted)",
            f"",
            f"✅ 최종승인 시 공개 전환됩니다.",
        ]
        return "\n".join(lines)
