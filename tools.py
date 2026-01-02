from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

from datetime import datetime, timedelta
import os
import json

import subprocess
import webbrowser

def open_app(app_name: str):
    subprocess.Popen(["open", "-a", app_name])

def search_web(query: str):
    webbrowser.open(f"https://www.google.com/search?q={query}")


SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


def get_today_events():
    creds = None

    if os.path.exists("token.json"):
        try:
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        except Exception as e:
            print(f"Error loading credentials: {e}")
            creds = None

    # 1️⃣ No credentials at all → OAuth once
    if not creds:
        flow = InstalledAppFlow.from_client_secrets_file(
            "credentials.json", SCOPES
        )
        creds = flow.run_local_server(port=0)

    # 2️⃣ Expired but refreshable → silent refresh
    elif creds.expired and creds.refresh_token:
        creds.refresh(Request())

    # 3️⃣ Save token (always)
    with open("token.json", "w") as token:
        token.write(creds.to_json())

    try:
        service = build("calendar", "v3", credentials=creds)

        now = datetime.utcnow().isoformat() + "Z"
        end = (datetime.utcnow() + timedelta(days=1)).isoformat() + "Z"

        events_result = service.events().list(
            calendarId="primary",
            timeMin=now,
            timeMax=end,
            singleEvents=True,
            orderBy="startTime"
        ).execute()

        events = events_result.get("items", [])

        if not events:
            return "No events today."

        output = []
        for event in events:
            start_raw = event["start"].get("dateTime", event["start"].get("date"))
            
            # Format time
            if "T" in start_raw:
                dt = datetime.fromisoformat(start_raw.replace("Z", "+00:00"))
                start_formatted = dt.strftime("%I:%M %p")
            else:
                dt = datetime.fromisoformat(start_raw)
                start_formatted = "All day"
            
            summary = event.get("summary", "No title")
            location = event.get("location", "")
            description = event.get("description", "")
            
            line = f"{start_formatted} — {summary}"
            if location:
                line += f" @ {location}"
            
            output.append(line)

        return "\n".join(output)
        
    except Exception as e:
        return f"Error fetching calendar events: {e}"
