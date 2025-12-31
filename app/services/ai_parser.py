# app/services/ai_parser.py

import os
import json
from datetime import datetime, timedelta
from typing import List

from openai import OpenAI
from dotenv import load_dotenv

from app.schemas import MeetingRequest, User

# Load environment variables from .env
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def extract_json_from_text(text: str) -> dict:
    """
    Ensure we extract valid JSON even if the LLM wraps it with extra text.
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end != -1:
            return json.loads(text[start:end])
        raise ValueError(f"AI returned invalid JSON: {text}")


def parse_message_to_meeting_request(
    message: str,
    requester: User,
    other_participants: List[User],
) -> MeetingRequest:
    """
    AI-powered parser:
    Extracts title, start_time, end_time, location from natural language.
    """

    system_prompt = (
        "You are an AI that extracts meeting details from a casual message.\n\n"
        "Return ONLY valid JSON in this format:\n"
        "{\n"
        '  \"title\": \"string\",\n'
        '  \"start_time\": \"ISO8601\",\n'
        '  \"end_time\": \"ISO8601\",\n'
        '  \"location\": \"string\"\n'
        "}\n\n"
        "Rules:\n"
        "1. Default duration is 1 hour if end_time is unclear.\n"
        "2. If time is vague, choose a reasonable interpretation.\n"
        "3. If location is missing, set it to 'unspecified'.\n"
        f"CURRENT UTC TIME: {datetime.utcnow().isoformat()}\n"
    )

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message},
        ]
    )

    # NEW: Use .content (object attribute), not ["content"]
    raw_output = response.choices[0].message.content

    parsed = extract_json_from_text(raw_output)

    title = parsed.get("title", "Meeting")
    location = parsed.get("location", "unspecified")

    # Parse times safely
    try:
        start = datetime.fromisoformat(parsed["start_time"].replace("Z", "+00:00"))
    except Exception:
        raise ValueError("Invalid or missing start_time from AI: " + raw_output)

    try:
        end = datetime.fromisoformat(parsed["end_time"].replace("Z", "+00:00"))
    except Exception:
        # Fallback: 1-hour duration
        end = start + timedelta(hours=1)

    return MeetingRequest(
        requester=requester.model_dump(),
        other_participants=[p.model_dump() for p in other_participants],
        title=title,
        start_time=start,
        end_time=end,
        location=location,
        raw_message=message,
    )

# -----------------------------
# Multi-turn incremental parser
# -----------------------------

def parse_multi_turn_update(
    message: str,
    history: list[str],
    meeting_state: dict,
) -> dict:
    """
    Incrementally extract meeting fields from a conversational turn.

    Returns only fields that were confidently detected.
    Does NOT overwrite existing values unless new info is found.
    """

    system_prompt = f"""
You are an AI assistant helping schedule a meeting over chat.

Conversation so far:
{chr(10).join(history)}

Current meeting state:
{meeting_state}

From the latest message, extract ONLY newly provided information.
If a field is not mentioned, return null for it.

Return valid JSON with any of:
- start_time (ISO 8601 or null)
- end_time (ISO 8601 or null)
- location (string or null)
- confirmation (true/false/null)

Rules:
- If user says "yes", confirmation = true
- If user says "no", confirmation = false
- Assume 1 hour duration if end_time not specified
- Never guess dates wildly; use context when possible
- Output JSON only
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message},
        ],
    )

    raw_output = response.choices[0].message.content

    import json
    try:
        parsed = json.loads(raw_output)
    except Exception:
        # Safety: return nothing if model output is malformed
        return {}

    updates = {}

    if parsed.get("start_time"):
        updates["start_time"] = parsed["start_time"]

    if parsed.get("end_time"):
        updates["end_time"] = parsed["end_time"]

    if parsed.get("location"):
        updates["location"] = parsed["location"]

    if parsed.get("confirmation") is not None:
        updates["confirmation"] = parsed["confirmation"]

    return updates

from datetime import datetime, timedelta

def parse_multi_turn_update(message, history, meeting_state):
    text = message.lower()
    update = {}

    if "tomorrow" in text:
        start = datetime.utcnow() + timedelta(days=1)
        start = start.replace(hour=15, minute=0, second=0, microsecond=0)
        update["start_time"] = start
        update["end_time"] = start + timedelta(hours=1)

    if "at" in text:
        update["location"] = text

    return update
