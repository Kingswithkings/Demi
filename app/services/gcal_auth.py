from __future__ import annotations

"""
Lightweight wrapper that exposes the OAuth flow for Streamlit UI.
"""

from app.gcal_auth import main as run_oauth_flow

__all__ = ["run_oauth_flow"]
