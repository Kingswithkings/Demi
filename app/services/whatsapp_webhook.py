from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse

from app.schemas import MeetingRequest, User
from app.services.scheduler import schedule_meeting
from app.services.ai_parser import parse_multi_turn_update
from app.services.whatsapp_client import send_whatsapp_text
from app.services.whatsapp_memory import whatsapp_memory
from app.services.intent_detector import detect_meeting_intent, is_yes, is_no
from app.services.location_utils import extract_area
from app.services.location_suggester import suggest_location

router = APIRouter()

VERIFY_TOKEN = "demi_verify_token"  # must match Meta dashboard


# -------------------------------------------------
# WhatsApp Verification (GET)
# -------------------------------------------------
@router.get("/whatsapp")
async def whatsapp_verify(request: Request):
    params = request.query_params

    if (
        params.get("hub.mode") == "subscribe"
        and params.get("hub.verify_token") == VERIFY_TOKEN
    ):
        return PlainTextResponse(params.get("hub.challenge", ""))

    return PlainTextResponse("Verification failed", status_code=403)


# -------------------------------------------------
# WhatsApp Incoming Messages (POST)
# -------------------------------------------------
@router.post("/whatsapp")
async def whatsapp_webhook(request: Request):

    # ---- Safe JSON parsing ----
    try:
        payload = await request.json()
    except Exception:
        return {"status": "ignored_non_json"}

    sender_id = None
    text = None

    # Local testing payload
    if "from" in payload and "text" in payload:
        sender_id = payload["from"]
        text = payload["text"]["body"]

    # Meta Cloud API payload
    else:
        try:
            msg = payload["entry"][0]["changes"][0]["value"]["messages"][0]
            sender_id = msg["from"]
            text = msg["text"]["body"]
        except Exception:
            return {"status": "ignored_bad_payload"}

    # ---- Conversation memory ----
    whatsapp_memory.add_message(sender_id, text)
    session = whatsapp_memory.get(sender_id)
    state = session["state"]
    meeting = session["meeting"]

    # -------------------------------------------------
    # 1. Proactive intent detection
    # -------------------------------------------------
    if state == "idle" and detect_meeting_intent(text):
        whatsapp_memory.set_state(sender_id, "prompted")
        send_whatsapp_text(
            sender_id,
            "I noticed you might be planning a meeting. Should I schedule it? Reply YES or NO."
        )
        return {"status": "prompted"}

    # -------------------------------------------------
    # 2. YES / NO after prompt
    # -------------------------------------------------
    if state == "prompted":
        if is_yes(text):
            whatsapp_memory.set_state(sender_id, "collecting")
            send_whatsapp_text(sender_id, "Great. What time should we meet?")
            return {"status": "collecting"}

        if is_no(text):
            whatsapp_memory.reset(sender_id)
            send_whatsapp_text(sender_id, "Okay, I won’t schedule anything.")
            return {"status": "cancelled"}

        send_whatsapp_text(sender_id, "Please reply YES or NO.")
        return {"status": "waiting_yes_no"}

    # -------------------------------------------------
    # 3. Multi-turn extraction (time, date, etc.)
    # -------------------------------------------------
    parsed = parse_multi_turn_update(
        message=text,
        history=session["history"],
        meeting_state=meeting,
    )
    whatsapp_memory.update_meeting(sender_id, parsed)
    meeting = whatsapp_memory.get(sender_id)["meeting"]

    # -------------------------------------------------
    # 4. Ask for time if missing
    # -------------------------------------------------
    if not meeting.get("start_time"):
        send_whatsapp_text(sender_id, "What time should we meet?")
        return {"status": "waiting_time"}

    # -------------------------------------------------
    # 5. Suggest location
    # -------------------------------------------------
    if not meeting.get("location") and state != "awaiting_location":
        area = extract_area(" ".join(session["history"]))
        suggestion = suggest_location(area, 0)

        session["suggested_location"] = suggestion
        whatsapp_memory.set_state(sender_id, "awaiting_location")

        send_whatsapp_text(
            sender_id,
            f"Would this location work?\n📍 {suggestion}\nReply YES or type another place."
        )
        return {"status": "location_suggested"}

    # -------------------------------------------------
    # 6. Location response
    # -------------------------------------------------
    if state == "awaiting_location":
        if is_yes(text):
            whatsapp_memory.update_meeting(
                sender_id, {"location": session["suggested_location"]}
            )
        else:
            whatsapp_memory.update_meeting(sender_id, {"location": text})

        whatsapp_memory.set_state(sender_id, "confirming")

    # -------------------------------------------------
    # 7. Confirmation prompt
    # -------------------------------------------------
    if state == "confirming":
        send_whatsapp_text(
            sender_id,
            f"Please confirm:\n"
            f"🕒 {meeting['start_time']}\n"
            f"📍 {meeting['location']}\n"
            f"Reply YES or NO."
        )
        whatsapp_memory.set_state(sender_id, "final")
        return {"status": "awaiting_confirmation"}

    # -------------------------------------------------
    # 8. Final decision
    # -------------------------------------------------
    if state == "final":
        if is_yes(text):
            req = MeetingRequest(
                requester=User(
                    id=sender_id,
                    name="WhatsApp User",
                    handle=sender_id,
                ),
                other_participants=[],
                title="Meeting",
                start_time=meeting["start_time"],
                end_time=meeting["end_time"],
                location=meeting["location"],
                raw_message=" ".join(session["history"]),
            )

            scheduled = schedule_meeting(req)

            send_whatsapp_text(
                sender_id,
                f"✅ Meeting scheduled!\n"
                f"Title: {scheduled.title}\n"
                f"Time: {scheduled.start_time}\n"
                f"Location: {scheduled.location}\n"
                f"Calendar ID: {scheduled.google_event_id or 'Not synced'}"
            )

            whatsapp_memory.reset(sender_id)
            return {"status": "scheduled"}

        if is_no(text):
            whatsapp_memory.reset(sender_id)
            send_whatsapp_text(sender_id, "Okay, cancelled.")
            return {"status": "cancelled"}

        send_whatsapp_text(sender_id, "Please reply YES or NO.")
        return {"status": "waiting_final_confirmation"}
