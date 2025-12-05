from fastapi import FastAPI
from typing import List

from app.schemas import User, Meeting
from app.services.ai_parser import parse_message_to_meeting_request
from app.services.scheduler import schedule_meeting
from app.services.storage import storage


app = FastAPI(
    title="Demi – AI Scheduling Assistant",
    version="0.1.0",
)

# ----- Demo users (Kings & Blessed) -----

KINGS = User(
    id="user_kings",
    name="Kings",
    handle="kings_handle",
    email="kingsuthanaidogu@gmail.com"        # 👈 add your real email (same Gmail for Calendar)
)

BLESSED = User(
    id="user_blessed",
    name="Blessed",
    handle="blessed_handle",
    email="kings@1st-kings.com"     # 👈 add Blessed’s real email
)


@app.post("/demo/parse-and-schedule", response_model=Meeting)
def parse_and_schedule(message: str):
    """
    Demo endpoint:
    - Assume Kings is requester.
    - Assume Blessed is the other participant.
    - Parse message and schedule a meeting.
    """
    req = parse_message_to_meeting_request(
        message=message,
        requester=KINGS,
        other_participants=[BLESSED],
    )
    meeting = schedule_meeting(req)
    return meeting


@app.get("/meetings", response_model=List[Meeting])
def list_all_meetings():
    return storage.list_meetings()


@app.get("/meetings/{user_id}", response_model=List[Meeting])
def list_meetings_for_user(user_id: str):
    return storage.get_meetings_for_user(user_id)
