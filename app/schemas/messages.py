from dataclasses import dataclass, field
from typing import Any, Dict, Optional, List

from pydantic import BaseModel, Field


# ----------------------------
# Normalized inbound message
# ----------------------------

@dataclass
class NormalizedMessage:
    """
    Canonical message object used by DemiAgent.

    Safe defaults allow Streamlit buttons (YES/NO)
    to create messages without errors.
    """
    user_id: str
    thread_id: str
    text: str

    channel: str = "streamlit"          # whatsapp | web | api | slack | streamlit
    timezone: str = "Europe/London"
    metadata: Dict[str, Any] = field(default_factory=dict)


# ----------------------------
# Scheduling schemas
# ----------------------------

class MeetingRequest(BaseModel):
    """
    Payload expected by schedule_meeting tool.
    Matches DemiAgent + LLM contract.
    """
    action: str = Field(
        default="create",
        description="create | update | cancel"
    )

    title: str = Field(default="Meeting")

    start_iso: str = Field(
        description="ISO 8601 datetime string"
    )

    duration_minutes: int = Field(
        default=30,
        description="Meeting duration in minutes"
    )

    attendees: List[str] = Field(default_factory=list)
    location: str = Field(default="Not specified")

    confirmed: Optional[bool] = Field(
        default=None,
        description="Set to True only after user confirms"
    )


class Meeting(BaseModel):
    """
    Persisted / returned meeting object.
    """
    id: str
    title: str
    start_iso: str
    duration_minutes: int

    attendees: List[str] = Field(default_factory=list)
    location: Optional[str] = None
    notes: Optional[str] = None
