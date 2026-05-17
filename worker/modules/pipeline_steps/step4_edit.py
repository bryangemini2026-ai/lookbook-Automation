"""
STEP 4: 편집 에이전트

FFmpeg로 BGM/자막/인트로/아웃트로 자동 삽입.
플랫폼별 3버전 렌더링 (YouTube/Instagram/TikTok).
완료 → Telegram 전송 → ✅통과 / 🔄재편집 / ✏️수정요청
"""

from modules.telegram_approval import TelegramApproval, ApprovalResult
from clients.storage import LocalStorage


class Step4Edit:
    """편집 + Telegram 승인 단계."""

    PLATFORMS = {
        "youtube": {"width": 1080, "height": 1920, "max_duration": 60},
        "instagram": {"width": 1080, "height": 1350, "max_duration": 90},
        "tiktok": {"width": 1080, "height": 1920, "max_duration": 60},
    }

    def __init__(self, redis_client):
        self.redis = redis_client
        self.approval = TelegramApproval()
        self.storage = LocalStorage()

    def execute(self, video_path: str, job_id: str,
                product: dict = None, max_retries: int = 3) -> dict:
        """
        편집 + Telegram 승인 루프.

        1. FFmpeg로 BGM/자막/인트로/아웃트로 삽입
        2. 플랫폼별 3버전 렌더링
        3. Telegram 전송 + 승인
        """
        attempts = 0
        edit_requests = []

        while attempts < max_retries:
            attempts += 1

            # 1. 편집
            print(f"[Step4] 편집 시도 {attempts}/{max_retries}")
            edited_videos = self._edit_video(video_path, job_id)

            # 2. Telegram 승인
            caption = self._build_caption(product, attempts, edit_requests)
            result, edit_text = self.approval.request_approval(
                step="edit",
                job_id=job_id,
                caption=caption,
                video_path=list(edited_videos.values())[0] if edited_videos else video_path,
                timeout=600,
            )

            if result == ApprovalResult.APPROVE:
                return {"status": "approved", "videos": edited_videos, "attempts": attempts}
            elif result == ApprovalResult.RETRY:
                continue
            elif result == ApprovalResult.EDIT:
                edit_requests.append(edit_text)
                continue

        return {"status": "max_retries", "videos": {}, "attempts": attempts}

    def _edit_video(self, video_path: str, job_id: str) -> dict:
        """플랫폼별 편집."""
        # TODO: FFmpeg 편집 구현
        # 1. BGM 삽입
        # 2. 자막 삽입
        # 3. 인트로/아웃트로
        # 4. 플랫폼별 리사이즈
        return {"youtube": video_path, "instagram": video_path, "tiktok": video_path}

    def _build_caption(self, product, attempts, edit_requests):
        lines = [f"*✂️ 편집 완료*", f"", f"*시도:* {attempts}회"]
        if edit_requests:
            lines.append(f"*수정 이력:*")
            for i, r in enumerate(edit_requests, 1):
                lines.append(f"  {i}. {r}")
        lines.extend([f"", f"아래 버튼을 눌러 승인해주세요."])
        return "\n".join(lines)
