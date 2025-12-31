from __future__ import annotations

import os
from typing import Tuple


def check_calendar_connected(
    token_path: str = "token.json",
    credentials_path: str = "credentials.json",
    include_error_detail: bool = True,
) -> Tuple[bool, str]:
    """
    Returns (connected, message).

    Connected means:
      - token.json exists AND
      - a small Google Calendar API call works.

    This function does NOT run OAuth login. It only checks status.
    """

    # Quick local checks for clearer UX
    if not os.path.exists(credentials_path):
        return False, f"Not connected ⚠️ (Missing {credentials_path})"

    if not os.path.exists(token_path):
        return False, f"Not connected ⚠️ (Missing {token_path})"

    try:
        # Import from the Google Calendar service module
        from .google_calendar import get_calendar_service

        service = get_calendar_service()
        service.calendarList().list(maxResults=1).execute()

        return True, "Connected ✅"

    except Exception as e:
        # More helpful error output
        if include_error_detail:
            return False, f"Not connected ⚠️ ({type(e).__name__}: {e})"
        return False, f"Not connected ⚠️ ({type(e).__name__})"
