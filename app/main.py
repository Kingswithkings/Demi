from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List

from app.app_factory import build_agent
from app.runtime.handler import handle_message
from app.routes.chat import router as chat_router
from app.schemas.messages import NormalizedMessage

from app.schemas import User, Meeting
from app.services.ai_parser import parse_message_to_meeting_request
from app.services.scheduler import schedule_meeting
from app.services.storage import storage

# WhatsApp webhook router
from app.services.whatsapp_webhook import router as whatsapp_router


app = FastAPI(
    title="Demi – AI Scheduling Assistant",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent, tools = build_agent()


# ----------------------------------
# Register WhatsApp Webhook
# ----------------------------------
app.include_router(chat_router)
app.include_router(whatsapp_router, prefix="/webhooks")


# ----------------------------------
# Root Endpoint
# ----------------------------------
@app.get("/")
def root():
    return {
        "message": "Demi AI Scheduling Assistant is running successfully.",
        "docs": "/docs",
        "demo_parse_and_schedule": "/demo/parse-and-schedule",
        "list_meetings": "/meetings",
        "whatsapp_webhook": "/webhooks/whatsapp",
    }


# ----------------------------------
# Demo Users (Kings & Blessed)
# ----------------------------------
KINGS = User(
    id="user_kings",
    name="Kings",
    handle="kings_handle",
    email="kingsuthanaidogu@gmail.com",
)

BLESSED = User(
    id="user_blessed",
    name="Blessed",
    handle="blessed_handle",
    email="kings@1st-kings.com",
)


# ----------------------------------
# AI Parsing + Scheduling Demo
# ----------------------------------
@app.post("/demo/parse-and-schedule", response_model=Meeting)
async def parse_and_schedule(message: str):
    """
    Demo endpoint for testing AI scheduling without WhatsApp.
    """
    req = parse_message_to_meeting_request(
        message=message,
        requester=KINGS,
        other_participants=[BLESSED],
    )
    meeting = await schedule_meeting(req)
    return meeting


# ----------------------------------
# View All Meetings
# ----------------------------------
@app.get("/meetings", response_model=List[Meeting])
def list_all_meetings():
    return storage.list_meetings()


# ----------------------------------
# View Meetings for Specific User
# ----------------------------------
@app.get("/meetings/{user_id}", response_model=List[Meeting])
def list_meetings_for_user(user_id: str):
    return storage.get_meetings_for_user(user_id)


@app.post("/agent/run")
async def agent_run(payload: dict):
    """
    Unified agent endpoint: behaves the same as Streamlit.
    Expected payload keys: user_id, thread_id, text, channel (optional), timezone(optional), metadata(optional)
    """
    msg = NormalizedMessage(
        user_id=payload.get("user_id", "demo-user"),
        thread_id=payload.get("thread_id", "demo-thread"),
        text=payload.get("text", ""),
        channel=payload.get("channel", "api"),
        timezone=payload.get("timezone", "Europe/London"),
        metadata=payload.get("metadata", {}) or {},
    )
    return await handle_message(agent, tools, msg)

@app.post("/demo/agent")
async def demo_agent(message: str):
    msg = NormalizedMessage(
        user_id=KINGS.id,
        thread_id="demo-thread-agent",
        text=message,
        channel="api",
        timezone="Europe/London",
        metadata={"demo": True},
    )
    return await handle_message(agent, tools, msg)
