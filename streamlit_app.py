import streamlit as st
from datetime import datetime, date, time, timedelta

# Calendar integration
from app.services.calendar_status import check_calendar_connected
from app.services.gcal_auth import run_oauth_flow
from app.services.google_calendar import create_event_from_meeting, get_calendar_service

# ✅ Correct import (NO Participant)
from app.schemas.meeting import Meeting


# -----------------------------
# Page config
# -----------------------------
st.set_page_config(
    page_title="Demi — Scheduling Assistant",
    page_icon="🗓️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# Session State Init
# -----------------------------
def init_state():
    st.session_state.setdefault("thread_id", "local-demo-thread")
    st.session_state.setdefault("user_id", "kings")
    st.session_state.setdefault("view", "Chat")
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("pending_actions", [])
    st.session_state.setdefault(
        "draft",
        {
            "title": "",
            "date": None,
            "time": None,
            "duration_mins": 30,
            "mode": "In-person",
            "location": "",
            "attendees": [],
            "notes": "",
        },
    )
    st.session_state.setdefault(
        "integrations",
        {
            "calendar_connected": False,
            "whatsapp_connected": True,
            "llm_connected": True,
        },
    )
    st.session_state.setdefault("tool_trace", [])


init_state()

# ✅ compute real calendar connectivity each run
connected, calendar_msg = check_calendar_connected()
st.session_state.integrations["calendar_connected"] = connected


# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:
    st.markdown("## Demi")
    st.caption("Conversational scheduling command center")

    st.session_state.view = st.radio(
        "View",
        ["Chat", "Upcoming", "Pending Confirmations", "Logs", "Settings"],
        index=["Chat", "Upcoming", "Pending Confirmations", "Logs", "Settings"].index(
            st.session_state.view
        ),
    )

    st.divider()

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("New conversation", width="stretch"):
            st.session_state.messages = []
            st.session_state.pending_actions = []
            st.session_state.tool_trace = []
            st.session_state.draft = {
                "title": "",
                "date": None,
                "time": None,
                "duration_mins": 30,
                "mode": "In-person",
                "location": "",
                "attendees": [],
                "notes": "",
            }
            st.rerun()

    with col_b:
        if st.button("Clear logs", width="stretch"):
            st.session_state.tool_trace = []
            st.rerun()

    st.text_input("Search history", placeholder="Search messages…", key="history_search")

    st.divider()

    with st.expander("Integrations", expanded=True):
        st.write("Calendar:", calendar_msg)
        st.write(
            "WhatsApp:",
            "Connected ✅"
            if st.session_state.integrations["whatsapp_connected"]
            else "Not connected ⚠️",
        )
        st.write(
            "LLM:",
            "Connected ✅"
            if st.session_state.integrations["llm_connected"]
            else "Not connected ⚠️",
        )

        if not connected:
            st.caption("Connect your Google Calendar to enable scheduling.")
            if st.button("Connect Google Calendar", width="stretch"):
                run_oauth_flow()
                st.rerun()

    with st.expander("Preferences"):
        st.selectbox("Timezone", ["Europe/London", "UTC"], index=0, key="tz_pref")
        st.selectbox(
            "Default meeting duration", [15, 30, 45, 60], index=1, key="default_duration"
        )
        st.toggle("Ask for confirmation before acting", value=True, key="confirm_gate")


# -----------------------------
# Main layout
# -----------------------------
left, center, right = st.columns([0.22, 0.53, 0.25], gap="large")

with left:
    st.markdown("### Overview")
    st.metric("Pending confirmations", len(st.session_state.pending_actions))
    st.metric("Messages", len(st.session_state.messages))
    st.info("Tip: Add attendee emails if you want invite emails to be sent.")

with center:
    st.markdown("### Demi")
    st.caption("Ask → Confirm → Act")

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.write(m["content"])

    if st.session_state.view == "Chat":
        user_text = st.chat_input(
            "Type a request (e.g., 'Schedule a meeting with John next Tuesday at 3pm')…"
        )
        if user_text:
            st.session_state.messages.append({"role": "user", "content": user_text})

            assistant_reply = (
                "I can do that. Please confirm the details in the draft panel on the right, "
                "add attendee emails if needed, then click Confirm & Act."
            )
            st.session_state.messages.append({"role": "assistant", "content": assistant_reply})

            # Demo draft fill
            st.session_state.draft["title"] = "Meeting"
            st.session_state.draft["date"] = date.today()
            st.session_state.draft["time"] = datetime.now().time().replace(second=0, microsecond=0)
            st.session_state.draft["duration_mins"] = st.session_state.get("default_duration", 30)

            st.session_state.pending_actions.append(
                {
                    "type": "schedule_meeting",
                    "status": "needs_confirmation",
                    "summary": "Schedule meeting (draft ready)",
                    "created_at": datetime.utcnow().isoformat() + "Z",
                }
            )

            st.session_state.tool_trace.append(
                {
                    "tool": "intent_parse_stub",
                    "input": {"text": user_text},
                    "output": {"intent": "schedule_meeting", "confidence": 0.72},
                }
            )

            st.rerun()
    else:
        st.warning("Switch to the Chat view in the sidebar to send a new request.")


with right:
    st.markdown("### Context")
    st.caption("Drafts, confirmations, and structured details")

    tabs = st.tabs(["Draft", "Calendar", "Details"])

    # --- Draft Tab ---
    with tabs[0]:
        st.markdown("#### Meeting / Event Draft")

        with st.form("draft_form", clear_on_submit=False):
            title = st.text_input("Title", value=st.session_state.draft["title"])
            d = st.date_input("Date", value=st.session_state.draft["date"] or date.today())
            t = st.time_input("Time", value=st.session_state.draft["time"] or time(9, 0))
            duration = st.selectbox(
                "Duration (mins)",
                [15, 30, 45, 60, 90, 120],
                index=[15, 30, 45, 60, 90, 120].index(st.session_state.draft["duration_mins"]),
            )
            mode = st.selectbox(
                "Mode",
                ["In-person", "Video call", "Phone call"],
                index=["In-person", "Video call", "Phone call"].index(st.session_state.draft["mode"]),
            )
            location = st.text_input("Location / Link", value=st.session_state.draft["location"])
            attendees_text = st.text_input(
                "Attendees (comma-separated emails)",
                value=",".join(st.session_state.draft["attendees"]),
                help="Invites are only emailed to these addresses. Example: a@gmail.com, b@outlook.com",
            )
            notes = st.text_area("Notes", value=st.session_state.draft["notes"], height=100)

            c1, c2 = st.columns(2)
            with c1:
                save = st.form_submit_button("Save draft", width="stretch")
            with c2:
                confirm = st.form_submit_button("Confirm & Act", width="stretch")

        if save or confirm:
            st.session_state.draft.update(
                {
                    "title": title.strip(),
                    "date": d,
                    "time": t,
                    "duration_mins": duration,
                    "mode": mode,
                    "location": location.strip(),
                    "attendees": [x.strip() for x in attendees_text.split(",") if x.strip()],
                    "notes": notes.strip(),
                }
            )

            if confirm:
                if not connected:
                    st.error("Google Calendar is not connected. Use the sidebar to connect first.")
                    st.stop()

                if st.session_state.get("confirm_gate", True) and len(st.session_state.pending_actions) == 0:
                    st.warning("No pending action exists yet. Start from chat or create one.")
                    st.stop()

                draft = st.session_state.draft

                if not draft.get("date") or not draft.get("time"):
                    st.error("Please select a Date and Time before confirming.")
                    st.stop()

                start_dt = datetime.combine(draft["date"], draft["time"])
                end_dt = start_dt + timedelta(minutes=int(draft.get("duration_mins") or 30))

                attendees = [e.strip() for e in (draft.get("attendees") or []) if e and e.strip()]

                # ✅ Show exactly what will be sent
                st.info(f"DEBUG: Invites will be sent to: {attendees}")

                if not attendees:
                    st.warning(
                        "No attendee emails provided. Google Calendar will create the event, but no invite emails can be sent."
                    )

                meeting = Meeting(
                    id="local",
                    title=draft.get("title") or "Meeting",
                    start_time=start_dt.isoformat(),
                    end_time=end_dt.isoformat(),
                    attendees=attendees,
                    location=draft.get("location") or "",
                    notes=draft.get("notes") or "",
                )

                try:
                    created = create_event_from_meeting(meeting)

                    st.success("Meeting created ✅")
                    if created.html_link:
                        st.link_button("Open in Google Calendar", created.html_link, width="stretch")

                    # ✅ Read event back to confirm guests stored by Google
                    try:
                        svc = get_calendar_service()
                        ev = svc.events().get(calendarId="primary", eventId=created.event_id).execute()
                        guests = [a.get("email") for a in (ev.get("attendees") or []) if a.get("email")]
                        st.caption(f"DEBUG: Google stored guests: {guests}")
                    except Exception as read_err:
                        st.caption(f"DEBUG: Could not read event back: {type(read_err).__name__}: {read_err}")

                    st.info(
                        "If guests were stored but you still don't see email: check Gmail Updates/Spam, "
                        "or test with a different email account than the calendar owner."
                    )

                    if st.session_state.pending_actions:
                        st.session_state.pending_actions[0]["status"] = "confirmed"

                    st.session_state.tool_trace.append(
                        {
                            "tool": "google_calendar.create_event_from_meeting",
                            "input": {
                                "title": meeting.title,
                                "start": meeting.start_time,
                                "end": meeting.end_time,
                                "attendees": attendees,
                                "location": meeting.location,
                            },
                            "output": {
                                "eventId": created.event_id,
                                "htmlLink": created.html_link,
                            },
                        }
                    )

                except Exception as e:
                    st.error(f"Failed to create calendar event: {type(e).__name__}: {e}")
                    st.session_state.tool_trace.append(
                        {
                            "tool": "google_calendar.create_event_from_meeting",
                            "output": {"error": f"{type(e).__name__}: {e}"},
                        }
                    )

            st.rerun()

        if st.session_state.pending_actions:
            st.markdown("#### Pending")
            for a in st.session_state.pending_actions[:3]:
                st.write(f"- **{a['type']}** — {a['status']}")

    # --- Calendar Tab ---
    with tabs[1]:
        st.markdown("#### Upcoming")
        if not connected:
            st.warning("Google Calendar is not connected yet. Use the sidebar to connect.")
        else:
            st.success("Google Calendar connected.")
            st.info("Next: render real events here from Google Calendar API.")

        st.dataframe(
            [
                {"When": "Tomorrow 10:00", "Title": "Standup", "Where": "Teams"},
                {"When": "Fri 14:00", "Title": "Project sync", "Where": "Office"},
            ],
            width="stretch",
            hide_index=True,
        )

    # --- Details Tab ---
    with tabs[2]:
        st.markdown("#### Extracted Intent / Tool Trace")
        if st.session_state.tool_trace:
            st.json(st.session_state.tool_trace[-1])
        else:
            st.caption("No tool trace yet. Send a message in Chat.")
