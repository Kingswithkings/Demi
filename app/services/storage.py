# app/services/storage.py
from typing import Dict, List

from app.schemas import Meeting

class InMemoryStorage:
    def __init__(self):
        self.meetings: Dict[str, Meeting] = {}

    def save_meeting(self, meeting: Meeting) -> Meeting:
        self.meetings[meeting.id] = meeting
        return meeting

    def list_meetings(self) -> List[Meeting]:
        return list(self.meetings.values())

    def get_meetings_for_user(self, user_id: str) -> List[Meeting]:
        return [
            m for m in self.meetings.values()
            if any(u.id == user_id for u in m.participants)
        ]

storage = InMemoryStorage()
