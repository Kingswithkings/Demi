from dataclasses import dataclass
from typing import Any, Dict

@dataclass
class LLMState:
    reply_text: str
    actions: list[dict]

class StubLLM:
    async def next_step(self, *args: Any, **kwargs: Any) -> LLMState:
        return LLMState(
            reply_text="LLM stub active. Wire the real LLM client to enable full reasoning.",
            actions=[],
        )
