from __future__ import annotations

from app.agents.demi_agents import DemiAgent
from app.tools.registry import build_tools
from app.services.llm_client import build_llm_client


def build_agent() -> tuple[DemiAgent, dict]:
    tools = build_tools()
    llm = build_llm_client()
    agent = DemiAgent(llm_client=llm, tools=tools)
    return agent, tools
