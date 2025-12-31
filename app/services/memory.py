"""
Minimal in-memory store for agent context and pending actions.

We store per-(user_id, thread_id):
- facts: a dict of key -> value
- messages: optional list (kept for future chat history)
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

MemoryInput = Dict[str, Any]

# Internal store: (user_id, thread_id) -> {"facts": {...}, "messages": [...]}
_STORE: Dict[Tuple[str, str], Dict[str, Any]] = {}


def _key(payload: MemoryInput) -> Tuple[str, str]:
    return (
        str(payload.get("user_id") or ""),
        str(payload.get("thread_id") or ""),
    )


async def memory_get(payload: MemoryInput) -> Dict[str, Any]:
    """
    Return memory in a stable shape:
      {
        "messages": [...],
        "facts": [{"key": "...", "value": ...}, ...],
        ... (also mirrored as top-level keys for convenience)
      }
    """
    key = _key(payload)
    record = _STORE.get(key) or {"facts": {}, "messages": []}

    facts_dict: Dict[str, Any] = record.get("facts") or {}
    messages = record.get("messages") or []

    # Represent facts in both forms:
    # - facts: list of {key,value} (good for tracing)
    # - top-level keys (good for direct access)
    facts_list = [{"key": k, "value": v} for k, v in facts_dict.items()]

    out: Dict[str, Any] = {"messages": messages, "facts": facts_list}
    out.update(facts_dict)  # allow memory["pending_action"] directly
    return out


async def memory_put(payload: MemoryInput) -> Dict[str, Any]:
    """
    Upsert facts into store.

    Expected payload:
      {
        "user_id": "...",
        "thread_id": "...",
        "facts": [{"key": "...", "value": ...}, ...]
      }

    Returns updated memory in the same shape as memory_get().
    """
    key = _key(payload)
    record = _STORE.setdefault(key, {"facts": {}, "messages": []})

    facts: List[Dict[str, Any]] = payload.get("facts") or []
    facts_dict: Dict[str, Any] = record.setdefault("facts", {})

    for fact in facts:
        k = fact.get("key")
        if not k:
            continue
        facts_dict[str(k)] = fact.get("value")

    # Optional: if caller passes messages, we can store them (future use)
    if "messages" in payload and isinstance(payload["messages"], list):
        record["messages"] = payload["messages"]

    return await memory_get(payload)
