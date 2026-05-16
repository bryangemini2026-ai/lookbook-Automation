"""
Skills management API routes.
Reads distilled skills and tool seeds from disk.
"""

import os
import glob
from fastapi import APIRouter

router = APIRouter()

BRAIN_BASE = "/srv/lookbook"
SKILLS_DIR = os.path.join(BRAIN_BASE, "brain", "10_Wiki", "styles")
TOOL_SEEDS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "worker", "tool-seeds")


@router.get("/")
def list_skills():
    """List all distilled skills from brain."""
    skills = []
    if os.path.isdir(SKILLS_DIR):
        for f in sorted(glob.glob(os.path.join(SKILLS_DIR, "*.md"))):
            name = os.path.splitext(os.path.basename(f))[0]
            with open(f) as fh:
                content = fh.read()
            # Extract first non-empty line as description
            lines = [l.strip() for l in content.split("\n") if l.strip() and not l.startswith("#")]
            desc = lines[0][:100] if lines else ""
            skills.append({
                "name": name,
                "description": desc,
                "path": f,
                "type": "distilled",
            })
    return skills


@router.get("/tool-seeds")
def list_tool_seeds():
    """List all available tool seeds."""
    seeds = []
    base = os.path.abspath(TOOL_SEEDS_DIR)
    if os.path.isdir(base):
        for agent_dir in sorted(os.listdir(base)):
            agent_path = os.path.join(base, agent_dir)
            if not os.path.isdir(agent_path) or agent_dir.startswith("_"):
                continue
            for f in sorted(os.listdir(agent_path)):
                if f.endswith(".md"):
                    tool_name = f[:-3]
                    md_path = os.path.join(agent_path, f)
                    py_path = os.path.join(agent_path, f"{tool_name}.py")
                    with open(md_path) as fh:
                        content = fh.read()
                    # Extract purpose
                    purpose = ""
                    for line in content.split("\n"):
                        if line.startswith("## Purpose"):
                            next_lines = [l.strip() for l in content.split("\n")[content.split("\n").index(line)+1:] if l.strip() and not l.startswith("#")]
                            if next_lines:
                                purpose = next_lines[0][:100]
                            break
                    seeds.append({
                        "name": tool_name,
                        "agent": agent_dir,
                        "purpose": purpose,
                        "has_doc": True,
                        "has_code": os.path.exists(py_path),
                    })
    return seeds


@router.get("/tool-seeds/{agent_id}")
def list_agent_tool_seeds(agent_id: str):
    """List tool seeds for a specific agent."""
    base = os.path.abspath(TOOL_SEEDS_DIR)
    agent_path = os.path.join(base, agent_id)
    if not os.path.isdir(agent_path):
        return {"error": f"Agent '{agent_id}' not found"}, 404

    seeds = []
    for f in sorted(os.listdir(agent_path)):
        if f.endswith(".md"):
            tool_name = f[:-3]
            md_path = os.path.join(agent_path, f)
            py_path = os.path.join(agent_path, f"{tool_name}.py")
            with open(md_path) as fh:
                content = fh.read()
            purpose = ""
            for line in content.split("\n"):
                if line.startswith("## Purpose"):
                    next_lines = [l.strip() for l in content.split("\n")[content.split("\n").index(line)+1:] if l.strip() and not l.startswith("#")]
                    if next_lines:
                        purpose = next_lines[0][:100]
                    break
            seeds.append({
                "name": tool_name,
                "agent": agent_id,
                "purpose": purpose,
                "has_doc": True,
                "has_code": os.path.exists(py_path),
            })
    return seeds


@router.get("/decisions")
def get_decisions():
    """Get decision log from brain."""
    path = os.path.join(BRAIN_BASE, "brain", "_shared", "decisions.md")
    if os.path.exists(path):
        with open(path) as f:
            return {"content": f.read()}
    return {"content": "# Decision Log\n\nNo decisions recorded yet."}
