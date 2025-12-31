from typing import Dict, List
from app.schemas import Meeting

class InMemoryStorage:
    def __init__(self):
        self._meetings: Dict[str, Meeting] = {}

    def add_meeting(self, meeting: Meeting) -> None:
        self._meetings[meeting.id] = meeting

    def list_meetings(self) -> List[Meeting]:
        return list(self._meetings.values())

    def get_meetings_for_user(self, user_id: str) -> List[Meeting]:
        result = []
        for m in self._meetings.values():
            if any(u.id == user_id for u in m.participants):
                result.append(m)
        return result

storage = InMemoryStorage()
