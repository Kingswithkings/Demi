# app/services/ai_parser.py

from datetime import datetime, timedelta
from typing import Optional, List

from app.schemas import MeetingRequest, User


def parse_message_to_meeting_request(
    message: str,
    requester: User,
    other_participants: List[User]
) -> MeetingRequest:
    """
    SUPER SIMPLE parser.
    Later: replace with OpenAI / LLM parsing.
    """
    text = message.lower()

    # -------------------------
    # 1️⃣ PARSE TIME
    # -------------------------
    now = datetime.utcnow()
    proposed_time: Optional[datetime] = None

    if "tomorrow" in text and "3pm" in text:
        proposed_time = (now + timedelta(days=1)).replace(
            hour=15, minute=0, second=0, microsecond=0
        )
    elif "saturday" in text and "3pm" in text:
        # next Saturday at 3 PM
        days_ahead = (5 - now.weekday()) % 7  # 5 = Saturday
        if days_ahead == 0:
            days_ahead = 7
        proposed_time = (now + timedelta(days=days_ahead)).replace(
            hour=15, minute=0, second=0, microsecond=0
        )

    # Fallback: if no time parsed, set 1 hour from now
    if not proposed_time:
        proposed_time = now + timedelta(hours=1)

    start = proposed_time
    end = start + timedelta(hours=1)

    # -------------------------
    # 2️⃣ PARSE LOCATION
    # -------------------------
    location: Optional[str] = None

    if "stratford" in text:
        location = "Stratford"
    if "costa" in text:
        if location:
            location = f"{location} Costa"
        else:
            location = "Costa"

    # Fallback if no location found
    if not location:
        location = "To be decided"

    # -------------------------
    # 3️⃣ TITLE
    # -------------------------
    if other_participants:
        names = ", ".join(u.name for u in other_participants)
        title = f"Meeting with {names}"
    else:
        title = "Meeting"

    # -------------------------
    # 4️⃣ RETURN MeetingRequest
    # -------------------------
    return MeetingRequest(
        requester=requester,
        other_participants=other_participants,
        title=title,
        start_time=start,
        end_time=end,
        location=location,
        raw_message=message,
    )
