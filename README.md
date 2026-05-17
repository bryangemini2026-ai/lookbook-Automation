# Lookbook SNS Automation

![Version-v0.0.5](https://img.shields.io/badge/Version-v0.0.5-blue)
![License](https://img.shields.io/badge/License-MIT-green)

> **Current Version:** v0.0.5 | **Last Updated:** 2026-05-17

AI 기반 패션 룩북 콘텐츠 자동 생성 및 SNS 자동 포스팅 시스템.

## Features

- **Dual ComfyUI Server** — 이미지(:8188) / 비디오(:8288) 분리 운영, GPU 배타 관리
- **PipelineWorker** — 단일 프로세스 파이프라인 (생성 → 업스케일 → 릴 → SNS 내보내기)
- **Agent System** — 5개 AI 에이전트 (페르소나 + 전문 도구), CRUD 관리
- **Dashboard** — React + Vite 기반 관리 UI (GPU 제어, 작업 큐, 에이전트, 스킬)
- **Watch Folder** — 이미지 드롭 → 자동 작업 큐잉 (inotify)
- **24h Scheduler** — 브리핑, 트렌드 수집, 실패 재시도 자동 실행
- **Brain System** — 트렌드 데이터, 캠페인 결과, 의사결정 장기 축적
- **Telegram Bot** — 상태 확인, 서버 제어, 작업 알림
- **FFmpeg Reel Maker** — 이미지 → 릴 비디오 (줌/팬/페이드, GPU 불필요)

## Architecture

```
Computer A (Ubuntu GPU Server)
├── ComfyUI Image Server (:8188)
├── ComfyUI Video Server (:8288)
├── PipelineWorker
├── FastAPI Gateway (:8000)
├── Redis + SQLite
├── Telegram Bot
├── FFmpeg
└── Samba Shared Folder

Computer B (Windows Dashboard)
├── React + Vite Dashboard (:5173)
└── Samba Mount (Z: drive)
```

## Quick Start

### 1. GPU Server Setup (Computer A)

```bash
git clone https://github.com/bryangemini2026-ai/lookbook-Automation.git
cd lookbook-Automation
bash scripts/setup_gpu_server.sh
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your Telegram bot token, etc.
```

### 3. Start Services

```bash
# Core services
sudo systemctl start redis-server
sudo systemctl start lookbook-gateway
sudo systemctl start lookbook-worker
sudo systemctl start lookbook-watcher

# ComfyUI (manual start — only one at a time)
sudo systemctl start comfyui-image
# or
sudo systemctl start comfyui-video
```

### 4. Dashboard (Computer B)

```bash
cd dashboard
npm install
npm run dev
# Open http://localhost:5173
```

## Project Structure

```
├── gateway/                    # FastAPI API server
│   └── app/routes/             # Jobs, Agents, Skills, GPU Control
├── worker/                     # PipelineWorker + modules
│   ├── modules/                # Generation, Upscale, Video, SNS, Brain, Secretary
│   ├── clients/                # ComfyUI, Telegram, Storage
│   ├── tool-seeds/             # Agent-specific tools (modular)
│   ├── agents.py               # Agent definitions with personas
│   ├── pipeline.py             # Main pipeline orchestrator
│   ├── scheduler.py            # 24h autonomous scheduler
│   └── watcher.py              # Watch folder daemon
├── dashboard/                  # React + Vite frontend
│   └── src/pages/              # Dashboard, Generate, Queue, Agents, Skills, Settings
├── scripts/                    # Setup + systemd services
├── workflows/                  # ComfyUI workflow templates
└── ARCHITECTURE.md             # Full architecture documentation
```

## GPU Control

두 개의 ComfyUI 서버는 동시에 실행할 수 없습니다 (8GB VRAM).

```bash
# 상태 확인
bash scripts/gpu-guard.sh status

# 서버 전환 (자동으로 이전 서버 중지 + VRAM 정리)
bash scripts/gpu-guard.sh switch image
bash scripts/gpu-guard.sh switch video
```

대시보드 Settings 페이지에서도 버튼으로 제어 가능.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/jobs/` | GET/POST | 작업 목록 / 생성 |
| `/api/agents/` | GET/POST/PUT/DELETE | 에이전트 CRUD |
| `/api/skills/` | GET | 추출된 스킬 목록 |
| `/api/skills/tool-seeds` | GET | Tool Seed 목록 |
| `/api/control/gpu/status` | GET | GPU 상태 |
| `/api/control/gpu/switch/{target}` | POST | 서버 전환 |
| `/api/control/queue` | GET | 큐 상태 |
| `/docs` | GET | Swagger UI |

## Agents

| Agent | Name | Role |
|-------|------|------|
| 👗 | 스타 | Head of Style — 트렌드 분석, 스타일 가이드 |
| 📸 | 포토 | Lead Photographer — 촬영 기획, 프롬프트 최적화 |
| 🎨 | 에디 | Visual Editor — 업스케일, 색보정, 썸네일 |
| 📱 | 소셜 | SNS Manager — 포스팅, 해시태그, 캡션 |
| 📊 | 데이터 | Data Analyst — 성과 분석, A/B 테스트 |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI (Python) |
| Database | SQLite (WAL mode) |
| Queue | Redis |
| GPU Engine | ComfyUI (bare metal) |
| Frontend | React + Vite + Tailwind |
| Video | FFmpeg |
| Notifications | Telegram Bot |
| File Sharing | Samba |

## License

MIT

