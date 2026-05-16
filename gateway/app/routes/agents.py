"""
Agent management API routes.
Agents are stored in SQLite for full CRUD support.
Default agents are seeded on first run.
"""

import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.db import get_db

router = APIRouter()

# ── Schemas ──

class AgentCreate(BaseModel):
    id: str
    name: str
    role: str
    emoji: str = "🤖"
    color: str = "#6366f1"
    specialty: str = ""
    tagline: str = ""
    persona: str = ""
    tools: list[str] = []
    status: str = "active"

class AgentUpdate(BaseModel):
    name: str | None = None
    role: str | None = None
    emoji: str | None = None
    color: str | None = None
    specialty: str | None = None
    tagline: str | None = None
    persona: str | None = None
    tools: list[str] | None = None
    status: str | None = None

# ── Default Agents ──

DEFAULT_AGENTS = [
    {
        "id": "stylist", "name": "스타", "role": "Head of Style",
        "emoji": "👗", "color": "#E91E63",
        "specialty": "패션 트렌드 분석, 스타일 가이드, 룩북 컨셉 기획",
        "tagline": "트렌드를 읽고 브랜드의 비주얼을 설계합니다",
        "persona": "패션 트렌드에 민감하고 데이터 기반으로 스타일을 제안합니다. '사장님'이라고 부르고, 현재 트렌드를 근거로 컨셉을 설명합니다.",
        "tools": '["trend_analysis","style_guide","color_palette"]',
        "status": "active",
    },
    {
        "id": "photographer", "name": "포토", "role": "Lead Photographer",
        "emoji": "📸", "color": "#FF9800",
        "specialty": "룩북 촬영 기획, 조명·구도·무드 설정, ComfyUI 프롬프트 최적화",
        "tagline": "한 장의 사진으로 브랜드를 말합니다",
        "persona": "조명·구도·무드를 한 줄로 잡아냅니다. ComfyUI 프롬프트를 직접 작성할 때 구체적이고 시각적인 표현을 사용합니다.",
        "tools": '["lookbook_generate","prompt_optimize","reference_match"]',
        "status": "active",
    },
    {
        "id": "editor", "name": "에디", "role": "Visual Editor",
        "emoji": "🎨", "color": "#9C27B0",
        "specialty": "포스트 프로덕션, 업스케일, 색보정, 썸네일 제작, 릴els 편집",
        "tagline": "감각적이고 깔끔한 결과물을 만듭니다",
        "persona": "감각적이고 깔끔합니다. 썸네일은 반드시 시선을 끌어야 합니다. 색보정은 브랜드 톤에 맞게.",
        "tools": '["upscale","face_fix","color_grade","thumbnail","reel_edit"]',
        "status": "active",
    },
    {
        "id": "sns_manager", "name": "소셜", "role": "SNS Manager",
        "emoji": "📱", "color": "#4CAF50",
        "specialty": "인스타/틱톡/트위터 포스팅, 해시태그, 캡션, 예약, 인게이지먼트 분석",
        "tagline": "콘텐츠를 세상에 알립니다",
        "persona": "해시태그·캡션·타이밍에 강합니다. '사장님'이라 부르고 챙겨주는 느낌.",
        "tools": '["instagram_post","tiktok_post","hashtag_gen","caption_gen","schedule"]',
        "status": "active",
    },
    {
        "id": "analyst", "name": "데이터", "role": "Data Analyst",
        "emoji": "📊", "color": "#2196F3",
        "specialty": "성과 분석, engagement 추적, A/B 테스트, 트렌드 리포트",
        "tagline": "숫자로 말합니다. 추측은 없습니다",
        "persona": "숫자로 말합니다. 추측 금지, 데이터 기반으로만 판단합니다.",
        "tools": '["engagement_report","ab_test","competitor_analysis","trend_report"]',
        "status": "active",
    },
]


def _ensure_table():
    """Create agents table and seed defaults if empty."""
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            emoji TEXT DEFAULT '🤖',
            color TEXT DEFAULT '#6366f1',
            specialty TEXT DEFAULT '',
            tagline TEXT DEFAULT '',
            persona TEXT DEFAULT '',
            tools TEXT DEFAULT '[]',
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)
    # Seed defaults if empty
    count = db.execute("SELECT COUNT(*) FROM agents").fetchone()[0]
    if count == 0:
        for a in DEFAULT_AGENTS:
            db.execute(
                "INSERT OR IGNORE INTO agents (id, name, role, emoji, color, specialty, tagline, persona, tools, status) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (a["id"], a["name"], a["role"], a["emoji"], a["color"], a["specialty"], a["tagline"], a["persona"], a["tools"], a["status"]),
            )
    db.commit()
    db.close()


def _row_to_dict(row) -> dict:
    d = dict(row)
    if "tools" in d and isinstance(d["tools"], str):
        try:
            d["tools"] = json.loads(d["tools"])
        except json.JSONDecodeError:
            d["tools"] = []
    return d


# ── Endpoints ──

@router.get("/")
def list_agents():
    """List all agents."""
    _ensure_table()
    db = get_db()
    rows = db.execute("SELECT * FROM agents ORDER BY rowid").fetchall()
    db.close()
    return [_row_to_dict(r) for r in rows]


@router.get("/{agent_id}")
def get_agent(agent_id: str):
    """Get agent detail."""
    _ensure_table()
    db = get_db()
    row = db.execute("SELECT * FROM agents WHERE id=?", (agent_id,)).fetchone()
    db.close()
    if not row:
        raise HTTPException(status_code=404, detail="Agent not found")
    return _row_to_dict(row)


@router.post("/", status_code=201)
def create_agent(agent: AgentCreate):
    """Register a new agent."""
    _ensure_table()
    db = get_db()
    existing = db.execute("SELECT id FROM agents WHERE id=?", (agent.id,)).fetchone()
    if existing:
        db.close()
        raise HTTPException(status_code=409, detail=f"Agent '{agent.id}' already exists")
    db.execute(
        "INSERT INTO agents (id, name, role, emoji, color, specialty, tagline, persona, tools, status) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (agent.id, agent.name, agent.role, agent.emoji, agent.color, agent.specialty, agent.tagline, agent.persona, json.dumps(agent.tools), agent.status),
    )
    db.commit()
    row = db.execute("SELECT * FROM agents WHERE id=?", (agent.id,)).fetchone()
    db.close()
    return _row_to_dict(row)


@router.put("/{agent_id}")
def update_agent(agent_id: str, update: AgentUpdate):
    """Update an existing agent."""
    _ensure_table()
    db = get_db()
    existing = db.execute("SELECT * FROM agents WHERE id=?", (agent_id,)).fetchone()
    if not existing:
        db.close()
        raise HTTPException(status_code=404, detail="Agent not found")

    updates = []
    values = []
    for field, value in update.model_dump(exclude_none=True).items():
        if field == "tools":
            value = json.dumps(value)
        updates.append(f"{field}=?")
        values.append(value)

    if not updates:
        db.close()
        return _row_to_dict(existing)

    updates.append("updated_at=datetime('now')")
    values.append(agent_id)
    db.execute(f"UPDATE agents SET {', '.join(updates)} WHERE id=?", values)
    db.commit()
    row = db.execute("SELECT * FROM agents WHERE id=?", (agent_id,)).fetchone()
    db.close()
    return _row_to_dict(row)


@router.delete("/{agent_id}")
def delete_agent(agent_id: str):
    """Delete an agent."""
    _ensure_table()
    db = get_db()
    existing = db.execute("SELECT id FROM agents WHERE id=?", (agent_id,)).fetchone()
    if not existing:
        db.close()
        raise HTTPException(status_code=404, detail="Agent not found")
    db.execute("DELETE FROM agents WHERE id=?", (agent_id,))
    db.commit()
    db.close()
    return {"deleted": agent_id}


@router.get("/{agent_id}/tools")
def get_agent_tools(agent_id: str):
    """Get tools available for an agent."""
    _ensure_table()
    db = get_db()
    row = db.execute("SELECT tools FROM agents WHERE id=?", (agent_id,)).fetchone()
    db.close()
    if not row:
        raise HTTPException(status_code=404, detail="Agent not found")
    tools = json.loads(row["tools"]) if row["tools"] else []
    return [{"name": t, "agent": agent_id, "status": "available"} for t in tools]
