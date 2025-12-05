# app/services/google_calendar.py
from __future__ import annotations

import os.path
from datetime import datetime
from typing import Optional, List

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.schemas import Meeting

# Same scope as in gcal_auth.py
SCOPES = ["https://www.googleapis.com/auth/calendar"]


def _get_credentials() -> Credentials:
    """Load stored credentials from token.json."""
    creds: Optional[Credentials] = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        # For safety: try refresh if possible
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            raise RuntimeError(
                "No valid Google credentials. Run `python gcal_auth.py` first."
            )

    return creds


def get_calendar_service():
    """Build and return a Google Calendar service client."""
    creds = _get_credentials()
    service = build("calendar", "v3", credentials=creds)
    return service


def create_event_from_meeting(meeting: Meeting) -> str:
    """
    Create a Google Calendar event from a Meeting object.
    Returns the created event's ID.
    """
    service = get_calendar_service()

    timezone = "Europe/London"  # adjust if needed

    # Build attendees list from meeting participants (using their emails)
    attendees: List[dict] = []
    for p in meeting.participants:
        if p.email:
            attendees.append({"email": p.email})

    event_body = {
        "summary": meeting.title,
        "location": meeting.location or "",
        "description": meeting.source_message or "",
        "start": {
            "dateTime": meeting.start_time.isoformat(),
            "timeZone": timezone,
        },
        "end": {
            "dateTime": meeting.end_time.isoformat(),
            "timeZone": timezone,
        },
        "attendees": attendees,  # Google will email these people
        "reminders": {
            "useDefault": True,
        },
    }

    event = (
        service.events()
        .insert(calendarId="primary", body=event_body, sendUpdates="all")
        .execute()
    )

    return event.get("id")
