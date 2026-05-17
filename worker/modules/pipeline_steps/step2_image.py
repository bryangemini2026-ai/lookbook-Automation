"""
STEP 2: 이미지 생성 에이전트

ComfyUI ZIT+ZIB로 상품 착용 이미지 3프레임 생성.
생성 완료 → Telegram 전송 → ✅통과 / 🔄재생성 / ✏️수정요청

ZIT 파라미터:
  Steps: 8~9 (고정)
  CFG: 1.0 (절대 변경 금지)
  Sampler: res_multistep (실사)
  네거티브 프롬프트: 사용 금지
"""

import json
import time

from modules.telegram_approval import TelegramApproval, ApprovalResult
from modules.gpu_manager import GPUManager
from clients.comfyui import ComfyUIClient
from clients.storage import LocalStorage
from modules.brain import BrainModule


class Step2ImageGen:
    """
    이미지 생성 + Telegram 승인 단계.

    1. ComfyUI ZIT+ZIB로 3프레임 생성
    2. Telegram으로 이미지 전송 + 승인 버튼
    3. 결과에 따라:
       - ✅ 통과 → STEP 3 진행
       - 🔄 재생성 → seed 변경 후 재생성
       - ✏️ 수정요청 → 수정 내용 반영 후 재생성
    """

    # ZIT 룩북 프롬프트 템플릿
    PROMPT_TEMPLATE = """photorealistic, fashion lookbook, professional photography,
high quality, 8k, cinematic lighting, korean woman,
slim figure, beautiful face, {setting},
{clothing_description},
sharp focus, detailed fabric, editorial fashion style,
natural pose, confident expression"""

    SETTINGS = {
        "spring": "garden, cherry blossom background, soft natural light",
        "summer": "beach, ocean background, golden hour lighting",
        "fall": "urban street, autumn leaves, warm tones",
        "winter": "studio, cozy interior, soft warm lighting",
    }

    def __init__(self, redis_client):
        self.redis = redis_client
        self.approval = TelegramApproval()
        self.gpu = GPUManager(redis_client)
        self.comfyui = ComfyUIClient("http://localhost:8188")
        self.storage = LocalStorage()
        self.brain = BrainModule()

    def execute(self, product: dict, job_id: str, max_retries: int = 3) -> dict:
        """
        이미지 생성 + Telegram 승인 루프.

        Args:
            product: STEP 1에서 수집된 상품 정보
            job_id: 고유 작업 ID
            max_retries: 최대 재시도 횟수

        Returns:
            {
                "status": "approved" | "rejected",
                "images": [bytes, ...],
                "image_paths": [str, ...],
                "attempts": int,
                "edit_requests": [str, ...],
            }
        """
        season = product.get("season", "spring")
        clothing = product.get("name", "fashion outfit")
        brand = product.get("brand", "")

        # 프롬프트 생성
        prompt = self._build_prompt(clothing, brand, season)

        attempts = 0
        edit_requests = []
        seed = -1  # -1 = random

        while attempts < max_retries:
            attempts += 1

            # 1. GPU 이미지 서버 확인
            self.gpu.ensure_server("image")

            # 2. 이미지 생성 (3프레임)
            print(f"[Step2] 이미지 생성 시도 {attempts}/{max_retries}")
            images = self._generate_images(prompt, seed, job_id)

            if not images:
                print(f"[Step2] 이미지 생성 실패")
                continue

            # 3. Telegram 승인 요청
            caption = self._build_caption(product, attempts, edit_requests)
            result, edit_text = self.approval.request_approval(
                step="image_gen",
                job_id=job_id,
                caption=caption,
                images=images,
                timeout=600,  # 10분 대기
            )

            # 4. 결과 처리
            if result == ApprovalResult.APPROVE:
                # 승인됨 → 이미지 저장, STEP 3 진행
                paths = self.storage.save_images(job_id, "approved", images)
                self.brain.log_decision(
                    f"이미지 승인: {clothing}",
                    f"시도 {attempts}회, 상품: {product.get('product_url', '')}"
                )
                return {
                    "status": "approved",
                    "images": images,
                    "image_paths": paths,
                    "attempts": attempts,
                    "edit_requests": edit_requests,
                    "product": product,
                }

            elif result == ApprovalResult.RETRY:
                # 재생성 → seed 변경
                seed = int(time.time()) % 1000000
                print(f"[Step2] 재생성 요청 (새 seed: {seed})")
                continue

            elif result == ApprovalResult.EDIT:
                # 수정요청 → 프롬프트 수정 후 재생성
                edit_requests.append(edit_text)
                prompt = self._apply_edit(prompt, edit_text)
                print(f"[Step2] 수정요청: {edit_text}")
                continue

        # 최대 횟수 초과
        return {
            "status": "max_retries",
            "images": [],
            "image_paths": [],
            "attempts": attempts,
            "edit_requests": edit_requests,
            "product": product,
        }

    def _build_prompt(self, clothing: str, brand: str, season: str) -> str:
        """ZIT 룩북 프롬프트 생성."""
        setting = self.SETTINGS.get(season, self.SETTINGS["spring"])
        clothing_desc = clothing
        if brand:
            clothing_desc = f"{brand} {clothing}"

        return self.PROMPT_TEMPLATE.format(
            setting=setting,
            clothing_description=clothing_desc,
        )

    def _apply_edit(self, prompt: str, edit_text: str) -> str:
        """수정요청을 프롬프트에 반영."""
        # 수정 키워드 분석
        edit_lower = edit_text.lower()

        additions = []
        if any(w in edit_lower for w in ["배경", "background"]):
            additions.append(f"background: {edit_text}")
        if any(w in edit_lower for w in ["포즈", "pose", "자세"]):
            additions.append(f"pose: {edit_text}")
        if any(w in edit_lower for w in ["조명", "lighting", "빛"]):
            additions.append(f"lighting: {edit_text}")
        if any(w in edit_lower for w in ["표정", "expression", "얼굴"]):
            additions.append(f"expression: {edit_text}")

        if additions:
            return f"{prompt}, {', '.join(additions)}"
        else:
            return f"{prompt}, {edit_text}"

    def _generate_images(self, prompt: str, seed: int, job_id: str) -> list[bytes]:
        """
        ComfyUI ZIT+ZIB로 이미지 3장 생성.

        ZIT 파라미터 (절대 변경 금지):
        - Steps: 8~9
        - CFG: 1.0
        - Sampler: res_multistep
        - 네거티브 프롬프트: 사용 금지
        """
        # ZIT 워크플로우 로드
        workflow_path = "workflows/image/ZIT_lookbook_v1.json"

        # 워크플로우가 없으면 기본 ComfyUI 워크플로우 사용
        if not self._file_exists(workflow_path):
            print(f"[Step2] 워크플로우 없음: {workflow_path}, 기본 생성 사용")
            return self._generate_placeholder_images(job_id)

        # ZIT 파라미터 주입
        params = {
            "steps": 8,
            "cfg": 1.0,
            "width": 1024,
            "height": 1024,
            "seed": seed if seed >= 0 else -1,
        }

        # 3프레임 생성 (구도/중간/최종)
        images = []
        for frame in range(3):
            frame_prompt = self._get_frame_prompt(prompt, frame)
            try:
                result = self.comfyui.execute_workflow(
                    self._load_workflow(workflow_path),
                    timeout=120,
                )
                if result:
                    images.extend(result)
            except Exception as e:
                print(f"[Step2] 프레임 {frame+1} 생성 실패: {e}")

        return images

    def _get_frame_prompt(self, base_prompt: str, frame: int) -> str:
        """프레임별 프롬프트 변형."""
        frame_mods = {
            0: "full body shot, standing pose, front view",
            1: "three-quarter view, slight angle, natural pose",
            2: "close-up detail, fabric texture visible, editorial style",
        }
        mod = frame_mods.get(frame, "")
        return f"{base_prompt}, {mod}"

    def _build_caption(self, product: dict, attempts: int, edit_requests: list) -> str:
        """Telegram 메시지 캡션 생성."""
        lines = [
            f"*📸 이미지 생성 완료*",
            f"",
            f"*상품:* {product.get('name', 'N/A')}",
            f"*브랜드:* {product.get('brand', 'N/A')}",
            f"*가격:* {product.get('price', 0):,}원",
            f"*플랫폼:* {product.get('platform', 'N/A')}",
            f"",
            f"*시도:* {attempts}회",
        ]

        if edit_requests:
            lines.append(f"*수정 이력:*")
            for i, req in enumerate(edit_requests, 1):
                lines.append(f"  {i}. {req}")

        if product.get("affiliate_url"):
            lines.append(f"")
            lines.append(f"[상품 링크]({product['affiliate_url']})")

        lines.append(f"")
        lines.append(f"아래 버튼을 눌러 승인해주세요.")

        return "\n".join(lines)

    def _file_exists(self, path: str) -> bool:
        """파일 존재 확인."""
        import os
        return os.path.exists(path)

    def _load_workflow(self, path: str) -> dict:
        """워크플로우 JSON 로드."""
        with open(path) as f:
            return json.load(f)

    def _generate_placeholder_images(self, job_id: str) -> list[bytes]:
        """워크플로우 없을 때 플레이스홀더 이미지 생성."""
        from PIL import Image, ImageDraw, ImageFont
        import io

        images = []
        for i in range(3):
            img = Image.new('RGB', (1024, 1024), color=(200, 200, 200))
            draw = ImageDraw.Draw(img)
            draw.text((400, 500), f"Frame {i+1}\nPlaceholder", fill=(100, 100, 100))
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            images.append(buf.getvalue())

        return images
