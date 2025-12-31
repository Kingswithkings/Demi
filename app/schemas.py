from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class User(BaseModel):
    id: str
    name: str
    handle: str
    email: Optional[str] = None

class MeetingRequest(BaseModel):
    requester: User
    other_participants: List[User]
    title: str
    start_time: datetime
    end_time: datetime
    location: str
    raw_message: str

class Meeting(BaseModel):
    id: str
    title: str
    participants: List[User]
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    source_message: Optional[str] = None
    google_event_id: Optional[str] = None
