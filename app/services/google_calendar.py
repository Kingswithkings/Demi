# app/services/google_calendar.py
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Set

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

from app.schemas import Meeting  # uses attendees: list[str]

SCOPES = ["https://www.googleapis.com/auth/calendar"]
DEFAULT_TZ = "Europe/London"
DEFAULT_CALENDAR_ID = "primary"


@dataclass(frozen=True)
class CalendarCreateResult:
    event_id: str
    html_link: Optional[str] = None
    hangout_link: Optional[str] = None


# -----------------------------
# Credentials
# -----------------------------
def _load_credentials(token_path: str = "token.json") -> Optional[Credentials]:
    if os.path.exists(token_path):
        return Credentials.from_authorized_user_file(token_path, SCOPES)
    return None


def _save_credentials(creds: Credentials, token_path: str = "token.json") -> None:
    with open(token_path, "w") as f:
        f.write(creds.to_json())


def _get_credentials(token_path: str = "token.json") -> Credentials:
    creds = _load_credentials(token_path)

    if not creds:
        raise RuntimeError(
            f"No token found at '{token_path}'. Connect Google Calendar first."
        )

    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            _save_credentials(creds, token_path)
        else:
            raise RuntimeError(
                "Google token invalid and cannot be refreshed. Reconnect Calendar."
            )

    return creds


def get_calendar_service(token_path: str = "token.json"):
    creds = _get_credentials(token_path)
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


# -----------------------------
# Attendees (FIXED)
# -----------------------------
def _build_attendees(meeting: Meeting) -> List[Dict[str, str]]:
    """
    Converts meeting.attendees (List[str]) to Google Calendar format.
    """
    attendees: List[Dict[str, str]] = []
    seen: Set[str] = set()

    for email in meeting.attendees or []:
        e = (email or "").strip()
        if not e:
            continue

        e_lc = e.lower()
        if e_lc in seen:
            continue

        seen.add(e_lc)
        attendees.append({"email": e})

    return attendees


# -----------------------------
# Event creation
# -----------------------------
def create_event_from_meeting(
    meeting: Meeting,
    calendar_id: str = DEFAULT_CALENDAR_ID,
    timezone: str = DEFAULT_TZ,
    send_updates: str = "all",  # "all" | "externalOnly" | "none"
    token_path: str = "token.json",
) -> CalendarCreateResult:
    if not meeting.start_time or not meeting.end_time:
        raise ValueError("Meeting must include start_time and end_time")

    service = get_calendar_service(token_path)
    attendees = _build_attendees(meeting)

    event_body: Dict[str, Any] = {
        "summary": meeting.title or "Meeting",
        "location": meeting.location or "",
        "description": meeting.notes or "",
        "start": {"dateTime": meeting.start_time, "timeZone": timezone},
        "end": {"dateTime": meeting.end_time, "timeZone": timezone},
        "attendees": attendees,
        "reminders": {"useDefault": True},
    }

    created = (
        service.events()
        .insert(
            calendarId=calendar_id,
            body=event_body,
            sendUpdates=send_updates,  # ✅ THIS sends emails
        )
        .execute()
    )

    return CalendarCreateResult(
        event_id=created.get("id", ""),
        html_link=created.get("htmlLink"),
        hangout_link=created.get("hangoutLink"),
    )
