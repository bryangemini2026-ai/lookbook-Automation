"""
Tool Seed loader.

Loads and executes tools from the tool-seeds directory.
Each tool is a {agent}/{tool_name}.py file with a run() function.
"""

import importlib
import os


TOOL_SEEDS_DIR = os.path.dirname(__file__)


def load_tool(agent_id: str, tool_name: str):
    """
    Load a tool module from tool-seeds.

    Usage:
        tool = load_tool("stylist", "trend_analysis")
        result = tool.run(keywords=["fashion"])
    """
    module_path = os.path.join(TOOL_SEEDS_DIR, agent_id, f"{tool_name}.py")
    if not os.path.exists(module_path):
        raise FileNotFoundError(f"Tool not found: {agent_id}/{tool_name}")

    spec = importlib.util.spec_from_file_location(
        f"tool_seeds.{agent_id}.{tool_name}",
        module_path,
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def list_tools(agent_id: str = None) -> dict[str, list[str]]:
    """List all available tools, optionally filtered by agent."""
    tools = {}

    if agent_id:
        agent_dir = os.path.join(TOOL_SEEDS_DIR, agent_id)
        if os.path.isdir(agent_dir):
            tools[agent_id] = [
                f[:-3] for f in os.listdir(agent_dir)
                if f.endswith(".py") and f != "__init__.py"
            ]
    else:
        for agent in os.listdir(TOOL_SEEDS_DIR):
            agent_dir = os.path.join(TOOL_SEEDS_DIR, agent)
            if os.path.isdir(agent_dir) and agent != "__pycache__":
                tools[agent] = [
                    f[:-3] for f in os.listdir(agent_dir)
                    if f.endswith(".py") and f != "__init__.py"
                ]

    return tools
