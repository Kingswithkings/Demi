from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.schemas.messages import NormalizedMessage
from app.services.confirm import is_yes, is_no


@dataclass
class AgentResult:
    reply_text: str
    actions: List[Dict[str, Any]]


class DemiAgent:
    """
    Channel-agnostic AI agent that:
    - loads memory/context
    - resolves pending actions (YES/NO)
    - decides next step (ask vs act)
    - enforces confirmation gate
    - executes via tools only
    """

    def __init__(self, llm_client, tools: Dict[str, Any]):
        self.llm = llm_client
        self.tools = tools

        # Required tools contract (fail fast if misconfigured)
        required = {"memory_get", "memory_put"}
        missing = required - set(tools.keys())
        if missing:
            raise ValueError(f"Missing required tools: {sorted(missing)}")

    async def run(self, msg: NormalizedMessage) -> AgentResult:
        actions: List[Dict[str, Any]] = []

        # 1) Load memory for context continuity
        memory = await self.tools["memory_get"](
            {"thread_id": msg.thread_id, "user_id": msg.user_id}
        )
        actions.append(
            {"tool": "memory_get", "input": {"thread_id": msg.thread_id}, "output": memory}
        )

        # 1a) Resolve a pending action (confirmation flow)
        pending = _get_pending_action(memory)

        # Trace pending extraction so we can see why YES isn't working
        actions.append(
            {
                "tool": "pending_action_lookup",
                "input": {"thread_id": msg.thread_id, "user_id": msg.user_id},
                "output": pending,
            }
        )

        if pending is not None:
            pending_payload = pending.get("payload", {}) or {}
            pending_tool = pending.get("tool_name") or pending.get("type")  # backward compat

            # Normalize pending tool name
            if pending_tool == "pending_schedule":
                pending_tool = "schedule_meeting"

            # YES → execute pending tool
            if is_yes(msg.text):
                tool_fn = self.tools.get(pending_tool)
                if not tool_fn:
                    # Clear pending; we cannot execute this tool
                    await self._clear_pending(msg, actions)
                    return AgentResult(
                        reply_text=f"I can’t execute the pending action because tool '{pending_tool}' is not available.",
                        actions=actions,
                    )

                try:
                    tool_output = await tool_fn({**pending_payload, "confirmed": True})
                    actions.append(
                        {"tool": pending_tool, "input": pending_payload, "output": tool_output}
                    )
                    await self._clear_pending(msg, actions)
                    return AgentResult(
                        reply_text="Confirmed. Done — your request has been executed successfully.",
                        actions=actions,
                    )
                except Exception as e:
                    # Keep pending by default so user can retry or modify
                    actions.append(
                        {"tool": "pending_execute_error", "input": {"tool": pending_tool}, "output": str(e)}
                    )
                    return AgentResult(
                        reply_text=(
                            "I attempted to execute it but it failed. "
                            "Reply YES to try again, or NO to change the details."
                            f" (Error: {str(e)})"
                        ),
                        actions=actions,
                    )

            # NO → clear pending and ask what to change
            if is_no(msg.text):
                await self._clear_pending(msg, actions)
                return AgentResult(
                    reply_text="No problem. What would you like to change (date, time, duration, location, attendees)?",
                    actions=actions,
                )

            # neither yes nor no
            return AgentResult(
                reply_text="Please reply YES to confirm or NO to change the details.",
                actions=actions,
            )

        # 2) Let the LLM propose next action (tool call or user question)
        llm_state = await self.llm.next_step(
            user_text=msg.text,
            timezone=msg.timezone,
            channel=msg.channel,
            memory=memory,
        )

        # Trace initial LLM decision
        actions.append(
            {
                "tool": "llm_next_step_initial",
                "input": {
                    "user_text": msg.text,
                    "timezone": msg.timezone,
                    "channel": msg.channel,
                },
                "output": llm_state,
            }
        )

        # 3) Tool-calling loop (bounded)
        max_steps = 6
        for _ in range(max_steps):
            tool_call = llm_state.get("tool_call")
            if not tool_call:
                break

            tool_name = tool_call.get("name")
            tool_args = tool_call.get("args", {}) or {}

            if not tool_name:
                break

            # 3a) Confirmation gate for irreversible scheduling actions
            if tool_name == "schedule_meeting" and note_requires_confirmation(tool_args):
                await self._store_pending(msg, tool_name, tool_args, actions)
                return AgentResult(
                    reply_text=render_confirmation_prompt(tool_args, msg.timezone),
                    actions=actions,
                )

            # 3b) Execute tool
            tool_fn = self.tools.get(tool_name)
            if not tool_fn:
                return AgentResult(
                    reply_text=f"I’m missing the capability to run '{tool_name}'. Please try a different request.",
                    actions=actions,
                )

            tool_output = await tool_fn(tool_args)
            actions.append({"tool": tool_name, "input": tool_args, "output": tool_output})

            # 3c) Feed tool result back to LLM for the next step
            llm_state = await self.llm.next_step(
                user_text=msg.text,
                timezone=msg.timezone,
                channel=msg.channel,
                memory=memory,
                tool_result={"name": tool_name, "output": tool_output},
            )

            # Trace follow-up LLM decision
            actions.append(
                {
                    "tool": "llm_next_step_after_tool",
                    "input": {
                        "user_text": msg.text,
                        "timezone": msg.timezone,
                        "channel": msg.channel,
                        "tool_result_name": tool_name,
                    },
                    "output": llm_state,
                }
            )

        # 4) If LLM ended with a reply
        reply_text = llm_state.get("reply_text") or "Understood. Please share a bit more detail so I can proceed."
        return AgentResult(reply_text=reply_text, actions=actions)

    async def _store_pending(
        self,
        msg: NormalizedMessage,
        tool_name: str,
        tool_args: Dict[str, Any],
        actions: List[Dict[str, Any]],
    ) -> None:
        pending = {"tool_name": tool_name, "payload": tool_args}

        await self.tools["memory_put"](
            {
                "thread_id": msg.thread_id,
                "user_id": msg.user_id,
                "facts": [{"key": "pending_action", "value": serialize_json(pending)}],
            }
        )

        # Store the full pending object in trace (useful for UI)
        actions.append({"tool": "memory_put", "input": {"pending_action": pending}, "output": "stored"})

    async def _clear_pending(self, msg: NormalizedMessage, actions: List[Dict[str, Any]]) -> None:
        await self.tools["memory_put"](
            {
                "thread_id": msg.thread_id,
                "user_id": msg.user_id,
                "facts": [{"key": "pending_action", "value": ""}],
            }
        )
        actions.append({"tool": "memory_put", "input": {"pending_action": ""}, "output": "cleared"})


# ----------------------------
# Helper functions
# ----------------------------

def note_requires_confirmation(schedule_args: Dict[str, Any]) -> bool:
    action = schedule_args.get("action")
    confirmed = schedule_args.get("confirmed") is True
    irreversible = action in {"create", "update", "cancel"}
    return irreversible and not confirmed


def render_confirmation_prompt(schedule_args: Dict[str, Any], tz: str) -> str:
    title = schedule_args.get("title", "Meeting")
    start = schedule_args.get("start_iso", "")
    duration = schedule_args.get("duration_minutes", "")
    location = schedule_args.get("location", "Not specified")
    attendees = schedule_args.get("attendees", [])

    people = ", ".join(attendees) if attendees else "No attendees specified"
    return (
        "Here is what I’m about to schedule:\n"
        f"- Title: {title}\n"
        f"- Start: {start} ({tz})\n"
        f"- Duration: {duration} minutes\n"
        f"- Location: {location}\n"
        f"- Attendees: {people}\n\n"
        "Reply YES to confirm, or NO to change something."
    )


def serialize_json(obj: Any) -> str:
    import json
    return json.dumps(obj, ensure_ascii=False)


def deserialize_json(s: str) -> Any:
    import json
    return json.loads(s)


def _get_pending_action(memory: Any) -> Optional[Dict[str, Any]]:
    """
    Robust pending_action extractor.

    Supports memory shapes like:
      1) {"pending_action": "<json>"}
      2) {"facts": {"pending_action": "<json>"}}
      3) {"facts": [{"key": "pending_action", "value": "<json>"}]}
      4) {"messages": [{"key": "pending_action", "value": "<json>"}]}  (fallback)
    """
    if not isinstance(memory, dict):
        return None

    raw = None

    # 1) Top-level key
    if memory.get("pending_action"):
        raw = memory.get("pending_action")

    # 2) facts as dict
    if raw is None and isinstance(memory.get("facts"), dict):
        raw = memory["facts"].get("pending_action")

    # 3) facts as list of key/value
    if raw is None and isinstance(memory.get("facts"), list):
        for item in memory["facts"]:
            if isinstance(item, dict) and item.get("key") == "pending_action":
                raw = item.get("value")
                break

    # 4) fallback: messages list sometimes used as fact store
    if raw is None and isinstance(memory.get("messages"), list):
        for item in memory["messages"]:
            if isinstance(item, dict) and item.get("key") == "pending_action":
                raw = item.get("value")
                break

    if not raw:
        return None

    # If JSON string
    if isinstance(raw, str):
        raw = raw.strip()
        if not raw:
            return None
        try:
            return deserialize_json(raw)
        except Exception:
            return None

    # If already dict
    if isinstance(raw, dict):
        return raw

    return None
