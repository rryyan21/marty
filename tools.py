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


SCOPES = ["https://www.googleapis.com/auth/calendar"]


def get_calendar_service():
    """
    Returns an authenticated Google Calendar service.
    Handles OAuth flow and token refresh automatically.
    """
    creds = None

    if os.path.exists("token.json"):
        try:
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        except Exception as e:
            print(f"Error loading credentials: {e}")
            creds = None

    # 1️⃣ No credentials at all → OAuth once
    if not creds:
        if not os.path.exists("credentials.json"):
            raise FileNotFoundError("credentials.json not found. Please set up Google Calendar API credentials.")
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

    return build("calendar", "v3", credentials=creds)


def get_today_events():
    try:
        service = get_calendar_service()

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


def get_calendar_events_range(start_time: datetime, end_time: datetime):
    """
    Fetches all calendar events between start_time and end_time.
    Returns a list of event dictionaries with start/end times.
    """
    try:
        service = get_calendar_service()
        
        time_min = start_time.isoformat() + "Z"
        time_max = end_time.isoformat() + "Z"
        
        events_result = service.events().list(
            calendarId="primary",
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime"
        ).execute()
        
        return events_result.get("items", [])
    
    except Exception as e:
        raise Exception(f"Error fetching calendar events: {e}")


def insert_calendar_event(summary: str, start_time: datetime, end_time: datetime, description: str = ""):
    """
    Safely inserts a single calendar event.
    Only uses events().insert - never modifies or deletes existing events.
    """
    try:
        service = get_calendar_service()
        
        event = {
            "summary": summary,
            "description": description,
            "start": {
                "dateTime": start_time.isoformat(),
                "timeZone": "America/Los_Angeles",  # TODO: make configurable
            },
            "end": {
                "dateTime": end_time.isoformat(),
                "timeZone": "America/Los_Angeles",
            },
        }
        
        created_event = service.events().insert(
            calendarId="primary",
            body=event
        ).execute()
        
        return created_event.get("id")
    
    except Exception as e:
        raise Exception(f"Error inserting calendar event: {e}")


def add_calendar_event(start_dt, end_dt, title, description=""):
    """
    Simple wrapper to add a calendar event.
    Accepts Python datetime objects and converts them to RFC3339 format.
    Returns success message or error string.
    """
    try:
        event_id = insert_calendar_event(
            summary=title,
            start_time=start_dt,
            end_time=end_dt,
            description=description
        )
        return f"Success: Added event '{title}'"
    except Exception as e:
        return f"Error: {str(e)}"
