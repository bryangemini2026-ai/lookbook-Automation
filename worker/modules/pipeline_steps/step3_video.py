"""
STEP 3: 영상 생성 에이전트

Sulphur-2 I2V로 이미지→영상 변환.
완료 → Telegram 전송 → ✅통과 / 🔄재생성 / ✏️수정요청

8GB VRAM 설정:
  체크포인트: ltx-2.3-22b-dev-fp8.safetensors
  해상도: 768×1024 (9:16)
  프레임: 49~81 (2~3초)
  FPS: 24
"""

from modules.telegram_approval import TelegramApproval, ApprovalResult
from modules.gpu_manager import GPUManager
from clients.comfyui import ComfyUIClient
from clients.storage import LocalStorage


class Step3VideoGen:
    """
    영상 생성 + Telegram 승인 단계.

    1. STEP 2 승인된 이미지 → Sulphur-2 I2V
    2. Telegram으로 영상 전송 + 승인 버튼
    3. 결과에 따라:
       - ✅ 통과 → STEP 4 진행
       - 🔄 재생성 → 모션 파라미터 변경 후 재생성
       - ✏️ 수정요청 → 수정 반영 후 재생성
    """

    def __init__(self, redis_client):
        self.redis = redis_client
        self.approval = TelegramApproval()
        self.gpu = GPUManager(redis_client)
        self.comfyui = ComfyUIClient("http://localhost:8288")  # Video 서버
        self.storage = LocalStorage()

    def execute(self, approved_images: list[bytes], job_id: str,
                product: dict = None, max_retries: int = 3) -> dict:
        """
        영상 생성 + Telegram 승인 루프.

        Args:
            approved_images: STEP 2에서 승인된 이미지
            job_id: 고유 작업 ID
            product: 상품 정보
            max_retries: 최대 재시도 횟수
        """
        attempts = 0
        edit_requests = []

        while attempts < max_retries:
            attempts += 1

            # 1. GPU 비디오 서버 확인
            self.gpu.ensure_server("video")

            # 2. 영상 생성
            print(f"[Step3] 영상 생성 시도 {attempts}/{max_retries}")
            video_path = self._generate_video(approved_images[0], job_id)

            if not video_path:
                print(f"[Step3] 영상 생성 실패")
                continue

            # 3. Telegram 승인 요청
            caption = self._build_caption(product, attempts, edit_requests)
            result, edit_text = self.approval.request_approval(
                step="video_gen",
                job_id=job_id,
                caption=caption,
                video_path=video_path,
                timeout=600,
            )

            # 4. 결과 처리
            if result == ApprovalResult.APPROVE:
                return {
                    "status": "approved",
                    "video_path": video_path,
                    "attempts": attempts,
                    "edit_requests": edit_requests,
                }
            elif result == ApprovalResult.RETRY:
                print(f"[Step3] 재생성 요청")
                continue
            elif result == ApprovalResult.EDIT:
                edit_requests.append(edit_text)
                print(f"[Step3] 수정요청: {edit_text}")
                continue

        return {"status": "max_retries", "video_path": None, "attempts": attempts}

    def _generate_video(self, image_bytes: bytes, job_id: str) -> str:
        """
        Sulphur-2 I2V로 영상 생성.

        8GB VRAM 최적화:
        - 해상도: 768×1024
        - 프레임: 49
        - FPS: 24
        """
        # Sulphur-2 워크플로우 로드
        workflow_path = "workflows/video/sulphur_i2v.json"

        if not self._file_exists(workflow_path):
            print(f"[Step3] Sulphur-2 워크플로우 없음, FFmpeg 릴로 대체")
            return self._generate_ffmpeg_reel(image_bytes, job_id)

        # TODO: Sulphur-2 I2V 실행
        # 1. 이미지를 ComfyUI input에 저장
        # 2. Sulphur-2 워크플로우 실행
        # 3. 결과 영상 다운로드

        return None

    def _generate_ffmpeg_reel(self, image_bytes: bytes, job_id: str) -> str:
        """Sulphur-2 없을 때 FFmpeg 줌/팬 릴 생성."""
        from modules.video import VideoModule
        video = VideoModule(self.comfyui)

        try:
            video_bytes = video.ffmpeg_reel(
                images=[image_bytes],
                style="zoom_pan",
                duration=3.0,
                platform="reels",
            )
            path = self.storage.save_video(job_id, "reel", video_bytes)
            return path
        except Exception as e:
            print(f"[Step3] FFmpeg 릴 생성 실패: {e}")
            return None

    def _build_caption(self, product: dict, attempts: int, edit_requests: list) -> str:
        lines = [
            f"*🎬 영상 생성 완료*",
            f"",
            f"*상품:* {product.get('name', 'N/A') if product else 'N/A'}",
            f"*시도:* {attempts}회",
        ]
        if edit_requests:
            lines.append(f"*수정 이력:*")
            for i, req in enumerate(edit_requests, 1):
                lines.append(f"  {i}. {req}")
        lines.append(f"")
        lines.append(f"아래 버튼을 눌러 승인해주세요.")
        return "\n".join(lines)

    def _file_exists(self, path: str) -> bool:
        import os
        return os.path.exists(path)
