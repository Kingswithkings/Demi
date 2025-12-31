from __future__ import annotations

from typing import Any, Dict, Optional
from dataclasses import asdict, is_dataclass

from app.schemas.messages import NormalizedMessage
from app.agents.demi_agents import AgentResult


async def post_run(actions: list[dict], tools: dict) -> None:
    """
    Put ALL side-effects here so Streamlit == FastAPI:
    - email notifications
    - WhatsApp notifications
    - logging
    - analytics
    """
    # Example pattern:
    # If schedule_meeting executed successfully, notify via email/whatsapp if you do that in API.
    for a in actions or []:
        if a.get("tool") == "schedule_meeting":
            meeting_out = a.get("output")
            # If you have an email tool, call it here
            notify = tools.get("send_email_notification")
            if notify:
                await notify({"event": "meeting_scheduled", "meeting": meeting_out})


async def handle_message(agent, tools: dict, msg: NormalizedMessage) -> Dict[str, Any]:
    """
    Single entry point used by BOTH FastAPI and Streamlit.
    Returns an API-style dict.
    """
    result: AgentResult = await agent.run(msg)

    # Run post-processing side effects (notifications, etc.)
    await post_run(result.actions, tools)

    return {
        "reply_text": result.reply_text,
        "actions": result.actions,
    }
