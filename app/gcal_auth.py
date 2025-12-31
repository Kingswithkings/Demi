# gcal_auth.py
from __future__ import print_function

import os.path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def run_oauth_flow(
    credentials_path: str = "credentials.json",
    token_path: str = "token.json",
    port: int = 0,
) -> Credentials:
    """
    Runs the Google OAuth consent flow and saves token.json.
    Use this from Streamlit when user clicks 'Connect Google Calendar'.
    """
    flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
    creds = flow.run_local_server(port=port)

    with open(token_path, "w") as token:
        token.write(creds.to_json())

    return creds


def load_credentials(
    token_path: str = "token.json",
) -> Optional[Credentials]:
    """
    Loads credentials from token.json if it exists.
    """
    if os.path.exists(token_path):
        return Credentials.from_authorized_user_file(token_path, SCOPES)
    return None


def get_calendar_service(
    token_path: str = "token.json",
    credentials_path: str = "credentials.json",
):
    """
    Returns a Google Calendar API service.
    - Uses token.json if available
    - Refreshes token if expired
    - If missing/invalid and no refresh token, runs OAuth flow
    """
    creds = load_credentials(token_path=token_path)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(token_path, "w") as token:
                token.write(creds.to_json())
        else:
            # No token yet (or cannot refresh) → run OAuth
            creds = run_oauth_flow(credentials_path=credentials_path, token_path=token_path)

    return build("calendar", "v3", credentials=creds)


def main():
    """Authorize Google Calendar and save token.json (CLI test)."""
    service = get_calendar_service()
    events_result = (
        service.events()
        .list(calendarId="primary", maxResults=1, singleEvents=True, orderBy="startTime")
        .execute()
    )
    events = events_result.get("items", [])

    if not events:
        print("Auth OK, no events found.")
    else:
        print("Auth OK. Example event:", events[0].get("summary"))


if __name__ == "__main__":
    main()
