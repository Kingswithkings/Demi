import os
import json
from typing import Any, Dict, Optional

from openai import AsyncOpenAI


class OpenAILLM:
    """
    LLM wrapper compatible with DemiAgent.

    DemiAgent expects:
      llm_state = await llm.next_step(user_text=..., timezone=..., channel=..., memory=..., tool_result=?)
      llm_state is a dict and supports .get("tool_call") and .get("reply_text")

    Output contract:
      {
        "reply_text": str,
        "tool_call": None OR {"name": str, "args": dict}
      }
    """

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def next_step(
        self,
        user_text: str,
        timezone: str,
        channel: str,
        memory: Any,
        tool_result: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        # Keep memory lightweight (avoid huge dumps)
        memory_snippet = self._safe_json(memory, max_chars=2500)
        tool_result_snippet = self._safe_json(tool_result, max_chars=1500) if tool_result else ""

        system = f"""
You are Demi, a scheduling assistant agent.

You MUST return a SINGLE JSON object and nothing else.

JSON schema:
{{
  "reply_text": string,
  "tool_call": null OR {{
    "name": string,
    "args": object
  }}
}}

TOOLS YOU MAY CALL:
- schedule_meeting: use when the user asks to create/update/cancel a meeting.
  schedule_meeting args MUST follow:
  {{
    "action": "create" | "update" | "cancel",
    "title": string,
    "start_iso": string,                // ISO 8601 datetime
    "duration_minutes": integer,
    "location": string,
    "attendees": [string],
    "confirmed": boolean (optional)     // usually omit; confirmation handled by agent
  }}

BEHAVIOR RULES:
- If the user intent is scheduling-related, set tool_call.name="schedule_meeting".
- Interpret phrases like "by 3pm today" as a meeting start time of 3pm today unless context suggests a deadline.
- If duration is missing, default duration_minutes=30.
- If title is missing, default title="Meeting".
- If location is missing, set location="Not specified".
- If attendees are not explicit, set attendees=[].
- If date/time is missing or cannot be inferred, ask a concise question via reply_text and set tool_call=null.
- Otherwise, call schedule_meeting with best-effort args.
- Use timezone "{timezone}" when interpreting ambiguous times (e.g., "today 4pm").
- Keep reply_text short and user-facing.
- channel="{channel}"

MEMORY (may be empty): {memory_snippet}
"""

        if tool_result:
            user = f"""User said: {user_text}

A tool just ran:
{tool_result_snippet}

Decide the next step and respond in the required JSON format."""
        else:
            user = f"""User said: {user_text}

Decide the next step and respond in the required JSON format."""

        resp = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system.strip()},
                {"role": "user", "content": user.strip()},
            ],
            temperature=0.1,
        )

        raw = (resp.choices[0].message.content or "").strip()

        # Parse strict JSON; if the model deviates, fail safe.
        try:
            data = json.loads(raw)
        except Exception:
            return {
                "reply_text": "I can help with that. Please confirm the date/time so I can proceed.",
                "tool_call": None,
                "raw": raw,
            }

        # Normalize output
        reply_text = str(data.get("reply_text") or "").strip()
        tool_call = data.get("tool_call")

        if tool_call is None:
            return {
                "reply_text": reply_text or "Understood. Please share a bit more detail so I can proceed.",
                "tool_call": None,
                "raw": raw,
            }

        if not isinstance(tool_call, dict):
            return {
                "reply_text": reply_text or "Please share a bit more detail so I can proceed.",
                "tool_call": None,
                "raw": raw,
            }

        name = tool_call.get("name")
        args = tool_call.get("args", {}) or {}

        if not name or not isinstance(args, dict):
            return {
                "reply_text": reply_text or "Please share a bit more detail so I can proceed.",
                "tool_call": None,
                "raw": raw,
            }

        # Defensive normalization: apply defaults if model omitted them
        # (This makes behavior stable and API-like.)
        if str(name) == "schedule_meeting":
            args.setdefault("duration_minutes", 30)
            args.setdefault("title", "Meeting")
            args.setdefault("location", "Not specified")
            if not isinstance(args.get("attendees"), list):
                args["attendees"] = []

        return {
            "reply_text": reply_text or "Okay.",
            "tool_call": {"name": str(name), "args": args},
            "raw": raw,
        }

    @staticmethod
    def _safe_json(obj: Any, max_chars: int = 2000) -> str:
        try:
            s = json.dumps(obj, ensure_ascii=False, default=str)
        except Exception:
            s = str(obj)
        if len(s) > max_chars:
            return s[:max_chars] + "…"
        return s


def build_llm_client() -> OpenAILLM:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is missing. Add it to your .env file.")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    return OpenAILLM(api_key=api_key, model=model)
