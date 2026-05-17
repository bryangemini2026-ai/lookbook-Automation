# Auto Deploy Setup Guide

GitHub에 코드를 push하면 자동으로 Computer A에 배포되는 설정 가이드.

---

## Overview

```
GitHub push → Actions → 버전 태그 → 릴리스 → 웹훅 전송 → Computer A 배포
```

사전 요구사항:
- Computer A에 Tailscale 설치 완료
- Gateway가 8000 포트에서 실행 중
- GitHub 저장소 관리자 권한

---

## Step 1: Tailscale IP 확인

Computer A에서 실행:

```bash
tailscale ip -4
```

출력 예시:
```
100.64.0.1
```

이 IP를 기록해둡니다.

---

## Step 2: Deploy Token 생성

아무 문자열이나 생성하면 됩니다. 터미널에서:

```bash
openssl rand -hex 32
```

출력 예시:
```
a1b2c3d4e5f6... (64자 문자열)
```

이 값을 **DEPLOY_TOKEN**으로 사용합니다. 기록해둡니다.

---

## Step 3: Computer A에 Token 설정

Computer A의 `.env` 파일에 추가:

```bash
# /opt/lookbook/.env (또는 프로젝트/.env)
DEPLOY_TOKEN=a1b2c3d4e5f6...  # Step 2에서 생성한 값
```

Gateway 재시작:
```bash
sudo systemctl restart lookbook-gateway
```

---

## Step 4: GitHub Secrets 설정

### 4-1. GitHub 저장소 열기

브라우저에서:
```
https://github.com/bryangemini2026-ai/lookbook-Automation
```

### 4-2. Settings 페이지로 이동

상단 탭에서 **Settings** 클릭

![Settings 위치]
```
Code | Issues | Pull requests | Actions | Projects | Wiki | Security | Insights | Settings
                                                                                    ↑ 여기
```

### 4-3. Secrets 메뉴 진입

왼쪽 사이드바에서:
```
Settings
├── General
├── Access
│   └── Collaborators and teams
├── Code and automation
│   ├── Branches
│   ├── Tags
│   ├── Webhooks
│   └── ...
├── Security
│   └── ...
└── Secrets and variables    ← 여기
    └── Actions              ← 여기 클릭
```

**Settings → Secrets and variables → Actions** 클릭

### 4-4. Secret 추가

**New repository secret** 버튼 클릭

#### 첫 번째 Secret: DEPLOY_WEBHOOK_URL

```
Name:    DEPLOY_WEBHOOK_URL
Value:   http://100.64.0.1:8000/api/system/deploy
```

> **중요**: Tailscale IP를 실제 값으로 변경하세요.
> HTTPS를 사용하는 경우: `https://100.64.0.1:443/api/system/deploy`

**Add secret** 클릭

#### 두 번째 Secret: DEPLOY_TOKEN

```
Name:    DEPLOY_TOKEN
Value:   a1b2c3d4e5f6...  (Step 2에서 생성한 값)
```

**Add secret** 클릭

### 4-5. 확인

Secrets 목록에 다음과 같이 표시되어야 합니다:

```
Name                    Value
──────────────────────  ──────────
DEPLOY_WEBHOOK_URL      http://100.64.0.1:8000/api/system/deploy
DEPLOY_TOKEN            ********
```

> Value는 마스킹 처리되어 보입니다. 정상입니다.

---

## Step 5: 동작 확인

### 5-1. 테스트 push

```bash
cd /home/ryan/문서/lookbook-sns-automation
echo "# test" >> README.md
git add README.md
git commit -m "test: auto deploy"
git push
```

### 5-2. GitHub Actions 확인

GitHub 저장소 → **Actions** 탭 클릭

```
https://github.com/bryangemini2026-ai/lookbook-Automation/actions
```

워크플로우 실행 상태 확인:
- ✅ Green = 성공
- ❌ Red = 실패 (클릭해서 로그 확인)

### 5-3. 릴리스 확인

GitHub 저장소 → **Releases** 탭

```
https://github.com/bryangemini2026-ai/lookbook-Automation/releases
```

새 버전이 자동 생성되어 있어야 합니다.

### 5-4. 배포 로그 확인

Actions 탭 → 최근 워크플로우 클릭 → **deploy** Job 확인

```
Trigger deploy webhook
  → Deploying version v0.0.2
  → Webhook sent successfully
```

---

## Troubleshooting

### 웹훅 전송 실패

**원인**: Computer A가 Tailscale 네트워크에 연결되지 않음

**해결**:
```bash
# Computer A에서
tailscale status
tailscale up
```

### 403 Forbidden

**원인**: DEPLOY_TOKEN 불일치

**해결**:
1. GitHub Secrets의 DEPLOY_TOKEN과 Computer A `.env`의 DEPLOY_TOKEN이 같은지 확인
2. 공백이나 줄바꿈이 없는지 확인

### Gateway 미실행

**원인**: Computer A에서 Gateway가 꺼져 있음

**해결**:
```bash
# Computer A에서
sudo systemctl start lookbook-gateway
curl http://localhost:8000/health
```

### 웹훅은 성공 but 배포 실패

**원인**: deploy.sh 스크립트 오류

**해결**:
```bash
# Computer A에서 수동 실행
bash /home/ryan/문서/lookbook-sns-automation/scripts/deploy.sh --status
bash /home/ryan/문서/lookbook-sns-automation/scripts/deploy.sh
```

---

## Advanced: 수동 배포

웹훅 없이 직접 배포:

```bash
# Computer A에서
cd /home/ryan/문서/lookbook-sns-automation
bash scripts/deploy.sh           # 전체 배포
bash scripts/deploy.sh --gateway # Gateway만 재시작
bash scripts/deploy.sh --worker  # Worker만 재시작
bash scripts/deploy.sh --status  # 현재 상태 확인
```

---

## Security Notes

- DEPLOY_TOKEN은 절대 Git에 커밋하지 마세요 (.env는 .gitignore에 포함)
- GitHub Secrets는 저장소 관리자만 볼 수 있습니다
- Tailscale VPN 외부에서는 웹훅에 접근할 수 없습니다
- 토큰이 유출되면 즉시 재생성하세요:
  ```bash
  openssl rand -hex 32  # 새 토큰 생성
  # GitHub Secrets 업데이트 + Computer A .env 업데이트
  ```
