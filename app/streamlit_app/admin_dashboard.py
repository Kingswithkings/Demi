import streamlit as st
from datetime import datetime, timezone
import pandas as pd
from dotenv import load_dotenv

from app.app_factory import build_agent
from app.schemas.messages import NormalizedMessage
from app.streamlit_app.st_agent_adapter import run_async

# Load environment variables before building the agent/LLM/tools
load_dotenv()

st.set_page_config(page_title="Demi Console", layout="wide")
st.title("Demi")

# ----------------------------
# Helpers
# ----------------------------
def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()

def extract_pending_from_actions(actions: list[dict]) -> dict | None:
    """
    Pull pending_action from memory_put action (stored) if present.
    """
    for a in reversed(actions or []):
        if a.get("tool") == "memory_put" and a.get("output") == "stored":
            pending = a.get("input", {}).get("pending_action")
            if isinstance(pending, dict):
                return pending
    return None

def extract_memory_from_actions(actions: list[dict]) -> dict | None:
    for a in reversed(actions or []):
        if a.get("tool") == "memory_get":
            out = a.get("output")
            if isinstance(out, dict):
                return out
    return None

def actions_table(actions: list[dict]) -> pd.DataFrame:
    rows = []
    for i, a in enumerate(actions or [], start=1):
        rows.append(
            {
                "#": i,
                "tool": a.get("tool"),
                "input": str(a.get("input"))[:3000],
                "output": str(a.get("output"))[:3000],
            }
        )
    return pd.DataFrame(rows)

def has_tool_execution(actions: list[dict]) -> bool:
    """
    Heuristic: if agent actually executed a tool, you should see entries other than memory_get/memory_put.
    Adjust this based on your tool naming conventions.
    """
    for a in actions or []:
        tool = (a.get("tool") or "").strip()
        if tool and tool not in {"memory_get", "memory_put"}:
            return True
    return False


# ----------------------------
# Agent + Tools (cached)
# ----------------------------
@st.cache_resource
def get_runtime():
    # build_agent() returns (agent, tools)
    return build_agent()

agent, tools = get_runtime()

# ----------------------------
# Session State
# ----------------------------
if "thread_id" not in st.session_state:
    st.session_state.thread_id = "demo-thread-001"
if "user_id" not in st.session_state:
    st.session_state.user_id = "demo-user-001"

if "chat" not in st.session_state:
    st.session_state.chat = []  # list of {role, content, ts, actions?}

if "pending" not in st.session_state:
    st.session_state.pending = None

if "_quick_text" not in st.session_state:
    st.session_state._quick_text = ""


# ----------------------------
# Sidebar (context)
# ----------------------------
with st.sidebar:
    st.header("Context")
    st.session_state.user_id = st.text_input("User ID", st.session_state.user_id)
    st.session_state.thread_id = st.text_input("Thread ID", st.session_state.thread_id)

    channel = st.selectbox("Channel", ["streamlit", "whatsapp"], index=0)

    st.divider()
    if st.button("Clear chat"):
        st.session_state.chat = []
        st.session_state.pending = None
        st.session_state._quick_text = ""
        st.rerun()

    # Optional: show current pending in sidebar
    if st.session_state.pending:
        st.divider()
        st.subheader("Pending (current)")
        st.json(st.session_state.pending)


# ----------------------------
# Render chat messages
# ----------------------------
for item in st.session_state.chat:
    with st.chat_message(item["role"]):
        st.markdown(item["content"])

        if item["role"] == "assistant" and item.get("actions"):
            with st.expander("Debug: tool trace", expanded=False):
                df = actions_table(item["actions"])
                if not df.empty:
                    st.dataframe(df, use_container_width=True, hide_index=True)

                mem = extract_memory_from_actions(item["actions"])
                if mem:
                    st.subheader("Memory snapshot")
                    st.json(mem)


# ----------------------------
# Quick replies (YES/NO) when pending exists
# ----------------------------
pending = st.session_state.pending
if pending:
    tool_name = pending.get("tool_name")
    payload = pending.get("payload", {})

    st.info("Confirmation needed. Use quick replies below (or type YES / NO).")
    with st.expander("View pending details", expanded=False):
        st.write(f"Tool: `{tool_name}`")
        st.json(payload)

    col_yes, col_no = st.columns(2)
    with col_yes:
        if st.button("YES — Confirm", type="primary", use_container_width=True):
            st.session_state._quick_text = "YES"
            st.rerun()

    with col_no:
        if st.button("NO — Change details", use_container_width=True):
            st.session_state._quick_text = "NO"
            st.rerun()


# ----------------------------
# Chat input
# ----------------------------
typed = st.chat_input("Type your message…")

# Allow quick reply injection
if st.session_state._quick_text:
    typed = st.session_state._quick_text
    st.session_state._quick_text = ""

if typed:
    # 1) Add user message
    st.session_state.chat.append({"role": "user", "content": typed, "ts": now_utc()})

    # 2) Run agent
    msg = NormalizedMessage(
        user_id=st.session_state.user_id,
        thread_id=st.session_state.thread_id,
        channel=channel,
        text=typed,
        timezone="Europe/London",
        metadata={"source": "streamlit_chat"},
    )

    with st.chat_message("assistant"):
        with st.spinner("Demi is thinking…"):
            result = run_async(agent.run(msg))

        st.markdown(result.reply_text)

        actions = result.actions or []

        # Update pending
        st.session_state.pending = extract_pending_from_actions(actions)

        # UX: show if a tool actually executed (helps diagnose invite emails)
        if typed.strip().upper() == "YES":
            if has_tool_execution(actions):
                st.success("Confirmed. Action executed.")
            else:
                st.warning(
                    "Confirmed, but no tool execution detected in trace. "
                    "This means your agent is not calling the calendar tool on YES yet."
                )

        st.session_state.chat.append(
            {
                "role": "assistant",
                "content": result.reply_text,
                "ts": now_utc(),
                "actions": actions,
            }
        )

    st.rerun()
