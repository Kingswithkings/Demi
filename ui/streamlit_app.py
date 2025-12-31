import streamlit as st
from datetime import datetime, date, time

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
    st.session_state.setdefault("messages", [])  # list[dict]: {"role": "user|assistant", "content": "..."}
    st.session_state.setdefault("pending_actions", [])  # list[dict]
    st.session_state.setdefault("draft", {
        "title": "",
        "date": None,
        "time": None,
        "duration_mins": 30,
        "mode": "In-person",
        "location": "",
        "attendees": [],
        "notes": "",
    })
    st.session_state.setdefault("integrations", {
        "calendar_connected": False,
        "whatsapp_connected": True,
        "llm_connected": True,
    })
    st.session_state.setdefault("tool_trace", [])  # list of tool calls/outputs for debug


init_state()

# -----------------------------
# Sidebar (Navigation + Control)
# -----------------------------
with st.sidebar:
    st.markdown("## Demi")
    st.caption("Conversational scheduling command center")

    st.session_state.view = st.radio(
        "View",
        ["Chat", "Upcoming", "Pending Confirmations", "Logs", "Settings"],
        index=["Chat", "Upcoming", "Pending Confirmations", "Logs", "Settings"].index(st.session_state.view),
    )

    st.divider()

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("New conversation", use_container_width=True):
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
    with col_b:
        if st.button("Clear logs", use_container_width=True):
            st.session_state.tool_trace = []

    st.text_input("Search history", placeholder="Search messages…", key="history_search")

    st.divider()

    with st.expander("Integrations", expanded=True):
        st.write("Calendar:", "Connected ✅" if st.session_state.integrations["calendar_connected"] else "Not connected ⚠️")
        st.write("WhatsApp:", "Connected ✅" if st.session_state.integrations["whatsapp_connected"] else "Not connected ⚠️")
        st.write("LLM:", "Connected ✅" if st.session_state.integrations["llm_connected"] else "Not connected ⚠️")

    with st.expander("Preferences"):
        st.selectbox("Timezone", ["Europe/London", "UTC"], index=0, key="tz_pref")
        st.selectbox("Default meeting duration", [15, 30, 45, 60], index=1, key="default_duration")
        st.toggle("Ask for confirmation before acting", value=True, key="confirm_gate")

# -----------------------------
# Main 3-Column Layout
# -----------------------------
left, center, right = st.columns([0.22, 0.53, 0.25], gap="large")

# Left column (optional summary tiles)
with left:
    st.markdown("### Overview")
    st.metric("Pending confirmations", len(st.session_state.pending_actions))
    st.metric("Messages", len(st.session_state.messages))
    st.info("Tip: Keep requests short. Demi will ask what’s missing.")

# Center column (Chat Workspace)
with center:
    st.markdown("### Demi")
    st.caption("Ask → Confirm → Act")

    # Render chat history
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.write(m["content"])

    # Chat input (only shown in Chat view)
    if st.session_state.view == "Chat":
        user_text = st.chat_input("Type a request (e.g., 'Schedule a meeting with John next Tuesday at 3pm')…")
        if user_text:
            st.session_state.messages.append({"role": "user", "content": user_text})

            # -----------------------------
            # TODO: Replace with your DemiAgent call
            # agent_result = await demi_agent.run(msg)
            # For now, stub a response + a pending action + draft fill
            # -----------------------------
            assistant_reply = (
                "I can do that. Please confirm the details in the draft panel on the right, "
                "then click Confirm."
            )
            st.session_state.messages.append({"role": "assistant", "content": assistant_reply})

            # Example: create a draft/pending action (replace with actual parsing output)
            st.session_state.draft["title"] = "Meeting"
            st.session_state.draft["date"] = date.today()
            st.session_state.draft["time"] = datetime.now().time().replace(second=0, microsecond=0)
            st.session_state.draft["duration_mins"] = st.session_state.get("default_duration", 30)

            st.session_state.pending_actions.append({
                "type": "schedule_meeting",
                "status": "needs_confirmation",
                "summary": "Schedule meeting (draft ready)",
                "created_at": datetime.utcnow().isoformat() + "Z",
            })

            # Tool trace stub
            st.session_state.tool_trace.append({
                "tool": "intent_parse_stub",
                "input": {"text": user_text},
                "output": {"intent": "schedule_meeting", "confidence": 0.72},
            })

            st.rerun()

    else:
        st.warning("Switch to the Chat view in the sidebar to send a new request.")

# Right column (Context Panel + Action Cards)
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
            duration = st.selectbox("Duration (mins)", [15, 30, 45, 60, 90, 120],
                                    index=[15, 30, 45, 60, 90, 120].index(st.session_state.draft["duration_mins"]))
            mode = st.selectbox("Mode", ["In-person", "Video call", "Phone call"], index=["In-person", "Video call", "Phone call"].index(st.session_state.draft["mode"]))
            location = st.text_input("Location / Link", value=st.session_state.draft["location"])
            attendees = st.text_input("Attendees (comma-separated emails)", value=",".join(st.session_state.draft["attendees"]))
            notes = st.text_area("Notes", value=st.session_state.draft["notes"], height=100)

            c1, c2 = st.columns(2)
            with c1:
                save = st.form_submit_button("Save draft", use_container_width=True)
            with c2:
                confirm = st.form_submit_button("Confirm & Act", use_container_width=True)

        if save or confirm:
            st.session_state.draft.update({
                "title": title.strip(),
                "date": d,
                "time": t,
                "duration_mins": duration,
                "mode": mode,
                "location": location.strip(),
                "attendees": [x.strip() for x in attendees.split(",") if x.strip()],
                "notes": notes.strip(),
            })

            if confirm:
                if st.session_state.get("confirm_gate", True) and len(st.session_state.pending_actions) == 0:
                    st.warning("No pending action exists yet. Start from chat or create one.")
                else:
                    # -----------------------------
                    # TODO: execute tool call here (schedule_meeting)
                    # -----------------------------
                    st.success("Confirmed. (Wire this to your tool execution layer.)")

                    # Mark first pending action as confirmed (demo)
                    if st.session_state.pending_actions:
                        st.session_state.pending_actions[0]["status"] = "confirmed"

                    st.session_state.tool_trace.append({
                        "tool": "confirm_stub",
                        "input": {"draft": st.session_state.draft},
                        "output": {"ok": True},
                    })

            st.rerun()

        # Show pending action summary
        if st.session_state.pending_actions:
            st.markdown("#### Pending")
            for a in st.session_state.pending_actions[:3]:
                st.write(f"- **{a['type']}** — {a['status']}")

    # --- Calendar Tab ---
    with tabs[1]:
        st.markdown("#### Upcoming (placeholder)")
        st.info("Wire this to Google Calendar read-only events once connected.")
        st.dataframe(
            [
                {"When": "Tomorrow 10:00", "Title": "Standup", "Where": "Teams"},
                {"When": "Fri 14:00", "Title": "Project sync", "Where": "Office"},
            ],
            use_container_width=True,
            hide_index=True,
        )

    # --- Details Tab ---
    with tabs[2]:
        st.markdown("#### Extracted Intent / Tool Trace")
        if st.session_state.tool_trace:
            st.json(st.session_state.tool_trace[-1])
        else:
            st.caption("No tool trace yet. Send a message in Chat.")
