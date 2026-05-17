# 룩북AI 프로젝트 문서
> aipage.studio | 작성일: 2026-05-17

---

## 1. 프로젝트 개요

### 목표
AI 기술을 활용한 완전 자동화 패션 룩북 콘텐츠 생산 및 멀티채널 수익화 시스템 구축

### 핵심 컨셉: "대신 입어드려요"
- 팔로워가 SNS 댓글에 쇼핑몰 옷 링크를 남기면 AI 모델이 착용한 이미지/영상을 자동 생성
- 어필리에이트 링크 자동 변환으로 추가 수익 확보
- 에이전트가 24/7 자동 운영

### 수익 4중 구조
| 수익원 | 방식 | 예상 (팔로워 10,000 기준) |
|---|---|---|
| 어필리에이트 | 무신사/쿠팡 링크 커미션 | 50~100만원/월 |
| B2C 착용 서비스 | 개인 요청 3,900원/건 | 20~50만원/월 |
| B2B 쇼핑몰 구독 | 월 29,900~99,000원 | 30~100만원/월 |
| 룩북 사이트 구독 | 팬 유료 구독 | 10~30만원/월 |

---

## 2. 하드웨어 환경

### 메인PC (AI 생산 서버)
| 항목 | 사양 |
|---|---|
| OS | Ubuntu 26.04 LTS (Resolute Raccoon) |
| CPU | AMD Ryzen 7 5700X (8코어/16스레드) |
| RAM | 48GB |
| GPU | RTX 3070Ti 8GB (NVIDIA 드라이버 580.142) |
| 저장장치 | NVMe 512GB (OS) + SU800 954GB (모델) + Samsung 830 119GB (백업) |
| 역할 | ComfyUI 전용 서버, 이미지/영상 생성, API Gateway, PipelineWorker |

### 서브PC (에이전트 오케스트레이터)
| 항목 | 사양 |
|---|---|
| OS | Windows 11 |
| CPU | Ryzen 1600X |
| RAM | 16GB |
| GPU | RX580 (AMD, CUDA 없음) |
| 역할 | 대시보드 UI, Samba 파일 접근, 에이전트 모니터링 |

### 네트워크
- Tailscale VPN으로 전 디바이스 연결
- 기가비트 LAN으로 메인PC↔서브PC 통신
- Tailscale IP: `100.121.36.8`

---

## 3. 디스크 구조 설계

```
[NVMe 512GB] - 속도 최우선
├── Ubuntu OS
├── ~/ComfyUI/                    (코드, 워크플로우)
├── ~/lookbook-sns-automation/     (자동화 시스템)
│   ├── gateway/                   (FastAPI API 서버)
│   ├── worker/                    (PipelineWorker + 모듈)
│   ├── dashboard/                 (React + Vite 대시보드)
│   ├── scripts/                   (설정 + systemd 서비스)
│   └── workflows/                 (ComfyUI 워크플로우 템플릿)
├── ~/openclaude/                  (OpenClaude CLI)
└── ~/scripts/                     (자동화 스크립트)

[SU800 954GB] - /mnt/models 마운트
└── /mnt/models/ComfyUI/
    ├── checkpoints/image/    (ZIB 베이스 모델)
    ├── checkpoints/video/    (LTX 2.3 영상 모델)
    ├── unet/image/           (ZIT GGUF 모델)
    ├── unet/video/           (Sulphur-2 GGUF)
    ├── loras/image/          (캐릭터 LoRA)
    ├── loras/video/          (영상 LoRA)
    ├── ipadapter/            (의상 참조)
    ├── controlnet/           (포즈 제어)
    ├── vae/
    ├── clip/
    └── output/
        ├── image/{pending, approved, rejected}
        └── video/{pending, approved, edited, uploaded}

[Samsung 830 119GB] - /mnt/backup 마운트
└── /mnt/backup/
    ├── workflows/
    ├── output/
    └── agents/
```

---

## 4. ComfyUI 설치 환경

### 설치 정보
- 방식: venv 독립 환경 (사실상 Portable과 동일)
- 위치: `~/ComfyUI/`
- Python: 3.14.4 (system)
- PyTorch: 2.12.0+cu130
- CUDA: True (RTX 3070Ti 정상 인식)

### 듀얼 ComfyUI 서버 (v3.0 신규)
8GB VRAM에서 안정성을 위해 이미지/비디오 서버를 분리 운영합니다.

| 서버 | 포트 | 용도 | 모델 |
|---|---|---|---|
| Image Server | 8188 | 이미지 생성 | ZIT, ZIB, SDXL, IPAdapter, Upscale |
| Video Server | 8288 | 영상 생성 | Sulphur-2, LTX 2.3, AnimateDiff |

**중요**: 두 서버는 동시에 실행할 수 없습니다 (8GB VRAM 제한).

### GPU 배타 관리 (gpu-guard.sh)
```bash
# 상태 확인
bash scripts/gpu-guard.sh status

# 서버 전환 (자동으로 이전 서버 중지 + VRAM 정리)
bash scripts/gpu-guard.sh switch image
bash scripts/gpu-guard.sh switch video
```

### 실행 명령어
```bash
# Image 서버
cd ~/ComfyUI && source venv/bin/activate
python main.py --listen 0.0.0.0 --port 8188 --lowvram

# Video 서버 (별도 설치)
cd ~/ComfyUI-video && source venv/bin/activate
python main.py --listen 0.0.0.0 --port 8288 --lowvram
```

### 접속 주소
- 메인PC: `http://localhost:8188` (이미지), `http://localhost:8288` (비디오)
- 서브PC: `http://메인PC_IP:8188`
- 태블릿(Tailscale): `http://100.121.36.8:8188`

### 설치된 커스텀 노드
| 노드 | 용도 |
|---|---|
| ComfyUI-Manager | 노드 통합 관리 |
| ComfyUI-KJNodes | GetNode (워크플로우 필수) |
| rgthree-comfy | Image Comparer |
| ComfyUI_IPAdapter_plus | 의상/캐릭터 참조 |
| comfyui_controlnet_aux | 포즈 추출 |
| ComfyUI-GGUF | GGUF 모델 로드 |

---

## 5. 이미지 생성 모델 (ZIT+ZIB)

### 모델 정보
- Z-Image-Turbo (ZIT): Alibaba Tongyi Lab, 6B DiT + 3.4B Qwen LLM 하이브리드
- Z-Image-Base (ZIB): 고품질 베이스 생성용

### 다운로드된 모델
| 파일명 | 위치 | 용도 |
|---|---|---|
| z_image_turbo_fp8_e4m3fn.safetensors | unet/image/ | ZIT FP8 |
| z-image-Q3_K_M.gguf | unet/image/ | ZIT Q3 (경량) |
| z-image-turbo-q3_k_m.gguf | unet/image/ | ZIT Q3 Turbo |
| qwen_3_4b.safetensors | clip/ | 텍스트 인코더 |
| ae.safetensors | vae/ | VAE |

### 생성 필수 파라미터
```
Steps:   8~9 (고정)
CFG:     1.0 (절대 변경 금지)
Sampler: res_multistep (실사) / euler_ancestral (애니)
네거티브 프롬프트: 사용 금지
```

### 워크플로우 구조 (ZIT_lookbook_v1.json)
```
Sampling 1 → 구도/초안/뼈대/컨셉
Sampling 2 → 얼굴/배경/세부 적용
Sampling 3 → 추가 정제
Sampling 4 → 최종 완성
⏸️ IP-Adapter → 의상 참조 (bypass, 모델 다운 후 활성화)
⏸️ ControlNet  → 포즈 제어 (bypass, 모델 다운 후 활성화)
```

---

## 6. 영상 생성 모델 (Sulphur-2 / LTX 2.3)

### 모델 정보
- Sulphur-2: LTX 2.3 기반 파인튜닝, 시네마틱 모션 특화
- I2V(Image-to-Video) 방식으로 ZIT 이미지를 영상으로 변환

### 8GB VRAM 구동 설정
```
체크포인트: ltx-2.3-22b-dev-fp8.safetensors
distill LoRA: ltx-2.3-22b-distilled-lora.safetensors
텍스트 인코더: gemma_3_12B_it_fp4_mixed.safetensors
실행 옵션: --lowvram --preview-method none
```

### 룩북 최적 파라미터
```
해상도: 768×1024 (9:16 세로형)
프레임: 49~81 (2~3초)
FPS: 24
모션: 낮게 (옷 디테일 보존 우선)
```

### 중요: 모델 전환 (8GB VRAM 동시 로드 불가)
```bash
# 영상 모드 전환 시 ZIT 모델 언로드 필수
curl -X POST http://localhost:8188/free \
     -d '{"unload_models": true, "free_memory": true}'
```

### FFmpeg 릴 메이커 (GPU 불필요)
이미지만으로 SNS 릴 비디오를 생성합니다.
```python
# worker/modules/video.py
styles = ["zoom_pan", "fade", "slide"]
platforms = {
    "instagram": "1080x1350",
    "reels": "1080x1920",
    "tiktok": "1080x1920",
    "twitter": "1200x675",
}
```

---

## 7. Simple Prompt Batcher 가이드

### 구조
```
최종 프롬프트 = Prepend + Prompts(각 줄) + Append
```

### 룩북 비키니/수영복 예시

**Prepend:**
```
photorealistic, fashion lookbook, professional photography,
high quality, 8k, cinematic lighting, korean woman,
slim figure, beautiful face, beach setting,
```

**Prompts (줄마다 1장):**
```
white bikini, standing on beach, ocean background, summer
black two-piece swimsuit, poolside, luxury resort background
floral bikini set, sandy beach, golden hour lighting
```

**Append:**
```
sharp focus, detailed fabric, editorial fashion style,
natural pose, confident expression
```

---

## 8. Lookbook SNS Automation 시스템 (v3.0 신규)

### 개요
FastAPI + React + Redis 기반의 룩북 자동화 시스템.
GitHub: https://github.com/bryangemini2026-ai/lookbook-Automation

### 아키텍처
```
메인PC (Ubuntu GPU 서버)
├── FastAPI Gateway (:8000)       ← API 서버
├── PipelineWorker                ← 작업 실행 엔진
├── Redis                         ← 작업 큐
├── SQLite                        ← 데이터베이스
├── ComfyUI Image (:8188)         ← 이미지 생성
├── ComfyUI Video (:8288)         ← 영상 생성
├── Telegram Bot                  ← 알림 + 원격 제어
├── FFmpeg                        ← 릴 비디오 제작
├── Samba                         ← 파일 공유
└── Watch Folder (inotify)        ← 자동 감지

서브PC (Windows)
├── React Dashboard (:5173)       ← 관리 UI
└── Samba Mount (Z:)              ← 파일 접근
```

### 핵심 API 엔드포인트
| 엔드포인트 | 메서드 | 설명 |
|---|---|---|
| `/api/jobs/` | GET/POST | 작업 목록/생성 |
| `/api/agents/` | GET/POST/PUT/DELETE | 에이전트 CRUD |
| `/api/skills/` | GET | 추출된 스킬 |
| `/api/skills/tool-seeds` | GET | Tool Seed 목록 |
| `/api/control/gpu/status` | GET | GPU 상태 |
| `/api/control/gpu/switch/{target}` | POST | 서버 전환 |
| `/api/system/version` | GET | 버전 정보 |
| `/api/system/deploy` | POST | 배포 웹훅 |
| `/docs` | GET | Swagger UI |

### 대시보드 페이지
| 페이지 | 기능 |
|---|---|
| Dashboard | GPU 상태, 큐 통계, 시스템 현황 |
| Generate | 프롬프트 입력, 워크플로우 선택, 이미지 생성 |
| Queue | 작업 목록, 상태 필터, 취소/재시도 |
| Agents | 에이전트 등록/수정/삭제, 페르소나 관리 |
| Skills | Tool Seeds, 추출된 스킬, 의사결정 로그 |
| Settings | GPU 서버 시작/중지/전환, 시스템 설정 |

---

## 9. 에이전트 시스템 (v3.0 신규)

### 에이전트 목록
| 에이전트 | 이름 | 역할 | 전문 분야 |
|---|---|---|---|
| 👗 | 스타 | Head of Style | 트렌드 분석, 스타일 가이드, 룩북 컨셉 기획 |
| 📸 | 포토 | Lead Photographer | 촬영 기획, 조명·구도·무드, ComfyUI 프롬프트 최적화 |
| 🎨 | 에디 | Visual Editor | 업스케일, 색보정, 썸네일, 릴 편집 |
| 📱 | 소셜 | SNS Manager | 포스팅, 해시태그, 캡션, 예약, 인게이지먼트 |
| 📊 | 데이터 | Data Analyst | 성과 분석, A/B 테스트, 트렌드 리포트 |

### 페르소나 시스템
각 에이전트는 고유한 말투와 전문성을 가집니다.
```python
# worker/agents.py
class AgentDef:
    id: str          # 고유 ID
    name: str        # 이름
    role: str        # 역할
    emoji: str       # 이모지
    color: str       # 색상
    specialty: str   # 전문 분야
    tagline: str     # 한 줄 설명
    persona: str     # 말투/성격
    tools: list      # 보유 도구
```

### Tool Seed 모듈화
각 에이전트별 도구를 `.md` + `.py` 쌍으로 모듈화합니다.
```
worker/tool-seeds/
├── stylist/trend_analysis.py       ← 트렌드 분석
├── photographer/lookbook_generate.py ← 룩북 생성
├── sns_manager/instagram_post.py   ← 인스타 포스팅
└── analyst/engagement_report.py    ← 성과 분석
```

### Secretary 게이트웨이
Telegram 메시지를 분류하여 적절한 에이전트로 라우팅합니다.
```
"안녕하세요" → reply (간단 답변)
"큐 상태 알려줘" → status (상태 조회)
"이미지 서버 시작해줘" → control (서버 제어)
"인스타에 올려줘" → dispatch → sns_manager
"트렌드 분석해줘" → dispatch → analyst
```

---

## 10. Brain 지식 축적 시스템 (v3.0 신규)

### 구조
```
data/lookbook/brain/
├── 00_Raw/                    ← 날짜별 데이터 (자동 수집)
│   └── 2026-05-17/
│       ├── trends.json        ← 트렌드 해시태그/스타일/컬러
│       └── jobs.jsonl         ← 작업 결과 로그
├── 10_Wiki/                   ← 구조화된 지식
│   └── styles/                ← 추출된 스킬 패턴
└── _shared/
    ├── identity.md            ← 브랜드 정체성
    └── decisions.md           ← 의사결정 로그
```

### 24시간 자율 스케줄러
```json
{
    "entries": [
        {"id": "morning-brief", "label": "모닝 브리핑", "hour": 9, "minute": 0},
        {"id": "evening-report", "label": "이브닝 리포트", "hour": 18, "minute": 0},
        {"id": "queue-retry", "label": "실패 큐 재시도", "hour": 3, "minute": 0},
        {"id": "brain-trend-collect", "label": "트렌드 데이터 수집", "hour": 2, "minute": 0}
    ]
}
```

### 스킬 디스틸
작업 완료 시 자동으로 성공 패턴을 추출하여 Brain에 저장합니다.
```
prompt_lookbook_portrait_20260517  ← 프롬프트 구조 패턴
style_lookbook_portrait_20260517   ← 스타일 파라미터 패턴
params_20260517                    ← 고품질 설정 패턴
```

---

## 11. CI/CD 파이프라인 (v3.0 신규)

### 자동 버전 관리
GitHub에 push할 때마다 자동으로 버전이 증가하고 릴리스가 생성됩니다.
```
git push → GitHub Actions → 버전 태그 → 릴리스 → 웹훅 → 자동 배포
```

### 현재 릴리스
```
v0.0.4 — Latest
v0.0.3
v0.0.2
v0.0.1
```

### 자동 배포
```bash
# Computer A에서
bash scripts/deploy.sh           # 전체 배포
bash scripts/deploy.sh --status  # 현재 상태 확인
bash scripts/deploy.sh --gateway # Gateway만 재시작
```

### 웹훅 보안
```bash
# .env 파일
DEPLOY_TOKEN=f8cb35ac0486972275f7705210f03e50890769a96133ed38ad8b3f26a568e468
```

---

## 12. Connect AI 에이전트 시스템

### 기반 오픈소스
- **Connect AI**: https://github.com/wonseokjung/connect-ai
- Antigravity VS Code 확장 프로그램
- 100% 로컬/오프라인/무료 (MIT 라이선스)

### 적용된 기능 (Lookbook 시스템 통합)
1. **에이전트 페르소나**: 각 에이전트에 고유한 말투/전문성 부여
2. **데일리 브리핑**: 매일 자동으로 Telegram으로 현황 보고
3. **24시간 자율 사이클**: 시간대별 자동 작업 실행
4. **Brain 시스템**: 트렌드 데이터, 캠페인 결과 장기 축적
5. **Tool Seed 모듈화**: 에이전트별 도구를 .md + .py 쌍으로 관리
6. **Secretary 게이트웨이**: Telegram 메시지 자동 분류/라우팅
7. **스킬 디스틸**: 성공 패턴 자동 추출 및 재활용

### 추가 개발 예정 기능
1. **외부 API 프로바이더**: NIM/Claude/OpenAI 추가
2. **NVIDIA NIM 설정 UI**: API 키 설정 + 연결 테스트
3. **에이전트 외부 API 선택**: 에이전트별 독립 프로바이더 설정
4. **크롤링 에이전트**: 무신사/쿠팡 신상 자동 수집

### NVIDIA NIM 병목 해소 전략
```
ComfyUI 작업 중 → LLM은 NIM API 자동 사용
ComfyUI 유휴 시 → 로컬 모델 우선
로컬 오프라인 시 → NIM 자동 폴백
```

---

## 13. OpenClaude 설치

### 정보
- **레포**: https://github.com/Gitlawb/openclaude
- Claude Code 오픈소스 대안, 멀티 프로바이더 지원
- 26.4k stars, MIT 라이선스

### 설치
```bash
npm install -g @gitlawb/openclaude
```

### 설정 파일 (~/.openclaude.json)
```json
{
  "agentModels": {
    "nim-llama": {
      "base_url": "https://integrate.api.nvidia.com/v1",
      "api_key": "NIM_API_KEY"
    },
    "local-qwen": {
      "base_url": "http://localhost:11434/v1",
      "api_key": "ollama"
    }
  },
  "agentRouting": {
    "코딩": "local-qwen",
    "분석": "nim-llama",
    "default": "local-qwen"
  }
}
```

---

## 14. SNS 전략 (홀모지 프레임워크 적용)

### 채널 운영 계획
| 채널 | 형식 | 목표 빈도 |
|---|---|---|
| YouTube Shorts | 60초 세로 영상 | 1개/일 |
| Instagram Reels | 90초 세로 영상 | 1개/일 |
| TikTok | 60초 세로 영상 | 1개/일 |

### 원소스 멀티유즈 전략
```
마스터 영상 1개 생성
├── YouTube: SEO 제목/설명, 어필리에이트 링크
├── Instagram: 해시태그 30개, 제품 태그
└── TikTok: 트렌딩 사운드, 짧은 훅 텍스트
```

### 하루 최대 생성 수량 (RTX 3070Ti 기준)
```
영상 1개 생성: ~11분
초기 (안정화): 3개/일 (채널당 1개)
안정화 후:     9개/일 (채널당 3개)
최대 권장:    15개/일 (채널당 5개)
```

### 가격 사다리
| 단계 | 상품 | 가격 |
|---|---|---|
| Free | SNS 맛보기 (워터마크) | 0원 |
| Low | 월 기본 구독 | 9,900원/월 |
| Mid | 프리미엄 구독 | 29,900원/월 |
| High | VIP (커스텀 무제한) | 99,000원/월 |

---

## 15. 어필리에이트 플랫폼

| 플랫폼 | 커미션율 | 쿠키 유지 | 특징 |
|---|---|---|---|
| 쿠팡 파트너스 | 최대 3% | 24시간 | 구매 전환율 최고 |
| 무신사 파트너스 | 2~5% | 30일 | 패션 특화, 단가 높음 |
| 29CM | 3~5% | 30일 | 고단가 브랜드 |
| 지그재그 | 2~4% | 7일 | 여성 패션 특화 |

---

## 16. 기술 스택 전체

| 역할 | 도구 | 비용 |
|---|---|---|
| API 서버 | FastAPI (Python) | 무료 |
| 데이터베이스 | SQLite (WAL 모드) | 무료 |
| 작업 큐 | Redis | 무료 |
| 프론트엔드 | React + Vite + Tailwind | 무료 |
| 이미지 생성 | ComfyUI + ZIT+ZIB | 무료 |
| 영상 생성 | Sulphur-2 / LTX 2.3 | 무료 |
| 릴 제작 | FFmpeg | 무료 |
| 에이전트 오케스트레이션 | PipelineWorker + Agent System | 무료 |
| 코딩 에이전트 CLI | OpenClaude | 무료 |
| 클라우드 LLM | NVIDIA NIM API | 무료 (할당량) |
| 승인 인터페이스 | Telegram Bot | 무료 |
| 파일 공유 | Samba | 무료 |
| CI/CD | GitHub Actions | 무료 |
| 원격 접속 | Tailscale | 무료 |
| **전체 운영비** | **전기세만** | |

---

## 17. 현재 진행 상태

### 완료 ✅
- [x] Ubuntu 26.04 설치
- [x] NVIDIA 드라이버 580.142 설치
- [x] SU800 ext4 포맷 + /mnt/models 마운트
- [x] Samsung 830 /mnt/backup 마운트
- [x] 디렉토리 구조 생성
- [x] ComfyUI 설치 (PyTorch 2.12.0+cu130, CUDA 확인)
- [x] ComfyUI Manager 설치
- [x] 커스텀 노드 5종 설치
- [x] ZIT 모델 3종 다운로드 (unet/image/)
- [x] VAE, CLIP 모델 다운로드
- [x] ZIT 룩북 워크플로우 로드
- [x] **Lookbook SNS Automation 시스템 구축** (v3.0)
- [x] **FastAPI Gateway + SQLite + Redis**
- [x] **PipelineWorker (듀얼 ComfyUI 지원)**
- [x] **React + Vite 대시보드 (6개 페이지)**
- [x] **에이전트 시스템 (5개 에이전트, CRUD)**
- [x] **Tool Seed 모듈화 (4개 도구)**
- [x] **Brain 지식 축적 시스템**
- [x] **24시간 자율 스케줄러**
- [x] **Secretary 게이트웨이 (Telegram 분류)**
- [x] **스킬 디스틸 시스템**
- [x] **GPU 배타 관리 (gpu-guard.sh)**
- [x] **CI/CD 파이프라인 (GitHub Actions)**
- [x] **자동 버전 관리 + 릴리스**
- [x] **배포 웹훅 + 토큰 보안**

### 진행 중 🔄
- [ ] IP-Adapter 모델 다운로드 → bypass 해제
- [ ] ControlNet 모델 다운로드 → bypass 해제
- [ ] 첫 이미지 생성 테스트
- [ ] Telegram Bot 생성 및 연동
- [ ] Connect AI NIM API 기능 추가
- [ ] Samba 공유 폴더 설정
- [ ] Watch Folder 자동화 테스트

### 예정 📋
- [ ] Sulphur-2 / LTX 2.3 영상 모델 다운로드
- [ ] 캐릭터 LoRA 학습 (SDXL 기반, RTX 3070Ti)
- [ ] CatVTON 의상 피팅 노드 설치
- [ ] 무신사 크롤러 에이전트 개발
- [ ] 쿠팡 파트너스 + 무신사 어필리에이트 가입
- [ ] YouTube Data API 연동
- [ ] Instagram/TikTok API 연동
- [ ] 구독 사이트 구축

---

## 18. 주요 명령어 모음

### Lookbook 시스템 관련
```bash
# Gateway 시작
cd ~/lookbook-sns-automation/gateway
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Worker 시작
cd ~/lookbook-sns-automation/worker
source venv/bin/activate
python main.py

# 스케줄러 시작
python run_scheduler.py

# 대시보드 시작 (서브PC)
cd ~/lookbook-sns-automation/dashboard
npm run dev

# 배포
bash scripts/deploy.sh
bash scripts/deploy.sh --status
```

### GPU 서버 제어
```bash
# 상태 확인
bash scripts/gpu-guard.sh status

# 서버 전환
bash scripts/gpu-guard.sh switch image
bash scripts/gpu-guard.sh switch video

# systemd로 관리
sudo systemctl start comfyui-image
sudo systemctl stop comfyui-image
sudo systemctl start comfyui-video
sudo systemctl stop comfyui-video
```

### ComfyUI 관련
```bash
# 서버 시작
cd ~/ComfyUI && source venv/bin/activate
python main.py --listen 0.0.0.0 --port 8188 --lowvram

# 모델 폴더 확인
ls /mnt/models/ComfyUI/unet/image/
ls /mnt/models/ComfyUI/vae/
ls /mnt/models/ComfyUI/clip/

# VRAM 해제 (모델 전환 시)
curl -X POST http://localhost:8188/free \
     -d '{"unload_models": true, "free_memory": true}'
```

### 시스템 모니터링
```bash
nvidia-smi                          # GPU 상태
free -h                             # RAM 상태
df -h | grep mnt                    # 디스크 사용량
watch -n 1 'nvidia-smi && free -h'  # 실시간 모니터링
```

### 파일 이동
```bash
# 다운로드 파일 모델 폴더로 이동
mv ~/다운로드/파일명.gguf /mnt/models/ComfyUI/unet/image/
mv ~/다운로드/파일명.safetensors /mnt/models/ComfyUI/checkpoints/image/
```

### 자동 백업
```bash
rsync -av /mnt/models/ComfyUI/output/approved/ /mnt/backup/output/
rsync -av ~/ComfyUI/user/default/workflows/ /mnt/backup/workflows/
```

---

*문서 버전: v2.0 | 마지막 업데이트: 2026-05-17*
*변경사항: Lookbook SNS Automation 시스템, 에이전트 시스템, CI/CD 파이프라인, Brain 시스템 추가*
