"""
Secretary Gateway Pattern.

Classifies Telegram messages into reply/dispatch/action types.
Inspired by Connect AI's secretary-triage.md pattern.

Flow:
    Telegram message → Secretary classifies → route to correct handler

Classification:
    - reply: Simple question, answer directly
    - dispatch: Task request, route to appropriate agent
    - status: Status query, fetch and respond
    - control: System control (start/stop/switch)
"""

import json
import re


class SecretaryModule:
    """
    Message classifier and router.
    All incoming Telegram messages pass through here first.
    """

    # ── Pattern Definitions ──

    STATUS_PATTERNS = [
        r"상태", r"status", r"어때", r"어떄", r"어떻게",
        r"큐", r"queue", r"gpu", r"메모리", r"memory",
        r"돌아가", r"running", r"실행",
    ]

    CONTROL_PATTERNS = [
        r"시작", r"start", r"중지", r"stop", r"스위치", r"switch",
        r"켜", r"꺼", r"재시작", r"restart",
    ]

    DISPATCH_PATTERNS = [
        r"만들어", r"생성", r"generate", r"create", r"make",
        r"올려", r"포스팅", r"post", r"업로드", r"upload",
        r"분석해", r"분석", r"analyze", r"트렌드", r"trend",
        r"릴els", r"reel", r"비디오", r"video",
        r"디자인", r"design", r"스타일", r"style",
    ]

    # ── Agent Routing ──

    AGENT_KEYWORDS = {
        "stylist": ["스타일", "트렌드", "컨셉", "기획", "style", "trend", "concept"],
        "photographer": ["사진", "촬영", "생성", "generate", "photo", "lookbook"],
        "editor": ["편집", "업스케일", "보정", "edit", "upscale", "색감"],
        "sns_manager": ["포스팅", "인스타", "해시태그", "캡션", "post", "instagram", "sns"],
        "analyst": ["분석", "성과", "데이터", "engagement", "분석", "분석"],
    }

    def classify(self, message: str) -> dict:
        """
        Classify a Telegram message.

        Returns:
            {
                "type": "reply" | "dispatch" | "status" | "control",
                "agent": str | None,  # target agent for dispatch
                "intent": str,  # detected intent
                "original": str,  # original message
            }
        """
        msg = message.strip().lower()

        # Check status queries
        if self._match_any(msg, self.STATUS_PATTERNS):
            return {
                "type": "status",
                "agent": None,
                "intent": "status_query",
                "original": message,
            }

        # Check control commands
        if self._match_any(msg, self.CONTROL_PATTERNS):
            return {
                "type": "control",
                "agent": None,
                "intent": "system_control",
                "original": message,
            }

        # Check dispatch (task requests)
        if self._match_any(msg, self.DISPATCH_PATTERNS):
            agent = self._detect_agent(msg)
            return {
                "type": "dispatch",
                "agent": agent,
                "intent": "task_request",
                "original": message,
            }

        # Default: reply (simple conversation)
        return {
            "type": "reply",
            "agent": None,
            "intent": "conversation",
            "original": message,
        }

    def _match_any(self, text: str, patterns: list[str]) -> bool:
        """Check if text matches any pattern."""
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def _detect_agent(self, message: str) -> str | None:
        """Detect which agent should handle this message."""
        msg = message.lower()
        best_agent = None
        best_score = 0

        for agent_id, keywords in self.AGENT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in msg)
            if score > best_score:
                best_score = score
                best_agent = agent_id

        return best_agent

    def route(self, classification: dict) -> dict:
        """
        Generate routing instructions based on classification.

        Returns:
            {
                "action": "reply" | "dispatch" | "query_status" | "control",
                "handler": str,  # function/method name to call
                "agent": str | None,
                "args": dict,
            }
        """
        t = classification["type"]

        if t == "status":
            return {
                "action": "query_status",
                "handler": "handle_status",
                "agent": None,
                "args": {"query": classification["original"]},
            }

        if t == "control":
            return {
                "action": "control",
                "handler": "handle_control",
                "agent": None,
                "args": {"command": classification["original"]},
            }

        if t == "dispatch":
            agent = classification.get("agent") or "photographer"
            return {
                "action": "dispatch",
                "handler": f"dispatch_to_{agent}",
                "agent": agent,
                "args": {"task": classification["original"]},
            }

        # reply
        return {
            "action": "reply",
            "handler": "handle_reply",
            "agent": None,
            "args": {"message": classification["original"]},
        }


class SecretaryTelegramHandler:
    """
    Handles Telegram messages through the Secretary gateway.
    Integrates with the existing Telegram bot.
    """

    def __init__(self, redis_client):
        self.redis = redis_client
        self.secretary = SecretaryModule()

    def handle_message(self, message: str) -> dict:
        """
        Process an incoming Telegram message through the Secretary.

        Returns:
            {
                "response": str,  # text to send back
                "action": str,    # what was done
            }
        """
        classification = self.secretary.classify(message)
        routing = self.secretary.route(classification)

        t = classification["type"]

        if t == "status":
            return self._handle_status()

        if t == "control":
            return self._handle_control(message)

        if t == "dispatch":
            return self._handle_dispatch(classification, routing)

        # reply — simple conversation
        return {
            "response": self._generate_reply(message),
            "action": "reply",
        }

    def _handle_status(self) -> dict:
        """Handle status query."""
        pending = self.redis.llen("lookbook:queue:pending")
        running = self.redis.llen("lookbook:queue:running")
        failed = self.redis.llen("lookbook:queue:failed")

        response = (
            f"*Queue Status*\n"
            f"  Pending: {pending}\n"
            f"  Running: {running}\n"
            f"  Failed: {failed}"
        )
        return {"response": response, "action": "status"}

    def _handle_control(self, message: str) -> dict:
        """Handle system control commands."""
        msg = message.lower()

        if "시작" in msg or "start" in msg:
            if "비디오" in msg or "video" in msg:
                return {"response": "비디오 서버를 시작합니다...", "action": "start_video"}
            return {"response": "이미지 서버를 시작합니다...", "action": "start_image"}

        if "중지" in msg or "stop" in msg:
            if "비디오" in msg or "video" in msg:
                return {"response": "비디오 서버를 중지합니다...", "action": "stop_video"}
            return {"response": "이미지 서버를 중지합니다...", "action": "stop_image"}

        if "스위치" in msg or "switch" in msg:
            if "비디오" in msg or "video" in msg:
                return {"response": "비디오 서버로 전환합니다...", "action": "switch_video"}
            return {"response": "이미지 서버로 전환합니다...", "action": "switch_image"}

        return {"response": "명령을 이해하지 못했습니다.", "action": "unknown"}

    def _handle_dispatch(self, classification: dict, routing: dict) -> dict:
        """Handle task dispatch to agents."""
        agent = routing.get("agent", "photographer")
        task = classification["original"]

        # Enqueue as a job
        import uuid
        job_id = str(uuid.uuid4())

        self.redis.lpush("lookbook:queue:pending", json.dumps({
            "id": job_id,
            "source": "telegram",
            "prompt": task,
            "workflow": "lookbook_portrait",
            "params": {"steps": 25, "cfg": 7.0, "width": 1024, "height": 1024},
            "assigned_agent": agent,
        }))

        from agents import get_agent
        agent_def = get_agent(agent)
        agent_name = agent_def.name if agent_def else agent

        return {
            "response": f"{agent_name} 에이전트에게 작업을 배분했습니다.\nJob ID: `{job_id[:8]}`",
            "action": "dispatch",
        }

    def _generate_reply(self, message: str) -> str:
        """Generate a simple conversational reply."""
        msg = message.lower()

        if any(w in msg for w in ["안녕", "hi", "hello", "헬로"]):
            return "안녕하세요, 사장님! 무엇을 도와드릴까요?"

        if any(w in msg for w in ["고마", "감사", "thanks", "thank"]):
            return "천만에요, 사장님! 더 필요한 게 있으면 말씀하세요."

        if any(w in msg for w in ["뭐해", "뭐 하고", "what are you"]):
            return "룩북 자동화 시스템 대기 중입니다. 명령을 내려주세요!"

        return (
            "명령을 이해하지 못했습니다.\n\n"
            "사용 가능한 명령:\n"
            "- 상태 확인: '상태', '큐'\n"
            "- 서버 제어: '시작', '중지', '스위치'\n"
            "- 작업 생성: '사진 만들어줘', '포스팅 해줘'\n"
            "- 분석: '트렌드 분석', '성과 분석'"
        )
