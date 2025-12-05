# gcal_auth.py
from __future__ import print_function

import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def main():
    """Authorize Google Calendar and save token.json."""
    print("Starting Google Auth…")  # DEBUG LINE

    creds = None

    if os.path.exists("token.json"):
        print("Found existing token.json")
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    else:
        print("token.json not found")

    if not creds or not creds.valid:
        print("Credentials invalid or not found — starting auth flow…")

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)

        print("Saving new token.json")
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    print("Testing Calendar access…")

    service = build("calendar", "v3", credentials=creds)
    events_result = (
        service.events()
        .list(calendarId="primary", maxResults=1, singleEvents=True, orderBy="startTime")
        .execute()
    )
    events = events_result.get("items", [])

    print("Auth successful!")
    if not events:
        print("No upcoming events found.")
    else:
        print("Example event:", events[0].get("summary"))


if __name__ == "__main__":
    main()
