# app/services/scheduler.py
import uuid
from datetime import datetime, timedelta

from app.schemas import MeetingRequest, Meeting
from app.services.storage import storage
from app.services.google_calendar import create_event_from_meeting


def schedule_meeting(request: MeetingRequest) -> Meeting:
    """Persist a meeting and create a Google Calendar event when possible."""
    start_time: datetime = request.start_time or (
        datetime.utcnow().replace(hour=10, minute=0, second=0, microsecond=0)
        + timedelta(days=1)
    )
    end_time: datetime = request.end_time or (start_time + timedelta(minutes=60))

    meeting = Meeting(
        id=str(uuid.uuid4()),
        title=request.title,
        participants=[request.requester] + request.other_participants,
        start_time=start_time,
        end_time=end_time,
        location=request.location,
        source_message=request.raw_message,
        google_event_id=None,
    )

    try:
        meeting.google_event_id = create_event_from_meeting(meeting)
    except Exception as exc:
        # TODO: replace with structured logging once available
        print("Failed to create Google Calendar event:", exc)

    storage.save_meeting(meeting)
    return meeting
