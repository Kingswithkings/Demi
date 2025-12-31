# app/services/scheduler.py
from uuid import uuid4

from app.schemas.meeting import MeetingRequest, Meeting
from app.services.storage import storage

def schedule_meeting(req: MeetingRequest) -> Meeting:
    meeting = Meeting(
        id=str(uuid4()),
        title=req.title,
        participants=[req.requester, *req.other_participants],
        start_time=req.start_time,
        end_time=req.end_time,
        location=req.location,
        source_message=req.raw_message,
        google_event_id=None,
    )

    # Save first
    storage.add_meeting(meeting)

    # Push to Google Calendar (best-effort)
    try:
        from app.services.google_calendar import create_event_from_meeting
        event_id = create_event_from_meeting(meeting)
        meeting.google_event_id = event_id
        storage.add_meeting(meeting)  # overwrite/update stored meeting
        print("📅 Google Calendar event created:", event_id)
    except Exception as e:
        print("⚠️ Google Calendar sync failed:", e)

    print("✅ Meeting scheduled:", meeting)
    return meeting
