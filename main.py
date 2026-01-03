from brain import think, classify_confirmation
from tools import open_app, search_web, get_today_events, get_calendar_events_range, add_calendar_event
import sys
import time
from datetime import datetime, timedelta

planning_state = {
    "active": False,
    "task": None,
    "due_date": None,
    "total_hours": None,
    "work_blocks": None,
    "waiting_for_final_confirmation": False
}

ALLOWED_APPS = {
    "spotify": "Spotify",
    "safari": "Safari",
    "notes": "Notes",
    "chrome": "Google Chrome"
}
print("MARTY online...")


def typewriter(text, delay=0.03):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()  # newline at the end


def parse_due_date(due_date_str: str) -> datetime:
    """
    Parses relative date strings like "next week", "next Tuesday" into datetime.
    Returns a datetime object for the end of that day.
    """
    now = datetime.now()
    due_date_lower = due_date_str.lower()
    
    # Simple parsing - can be enhanced later
    if "next week" in due_date_lower:
        # Next week = 7 days from now, end of day
        target = now + timedelta(days=7)
        return target.replace(hour=23, minute=59, second=0, microsecond=0)
    elif "next tuesday" in due_date_lower:
        days_ahead = 1 - now.weekday()  # Tuesday is 1
        if days_ahead <= 0:
            days_ahead += 7
        target = now + timedelta(days=days_ahead)
        return target.replace(hour=23, minute=59, second=0, microsecond=0)
    elif "tuesday" in due_date_lower:
        days_ahead = 1 - now.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        target = now + timedelta(days=days_ahead)
        return target.replace(hour=23, minute=59, second=0, microsecond=0)
    else:
        # Default: 7 days from now
        target = now + timedelta(days=7)
        return target.replace(hour=23, minute=59, second=0, microsecond=0)


def time_overlaps(start1: datetime, end1: datetime, start2: datetime, end2: datetime) -> bool:
    """Check if two time ranges overlap."""
    return start1 < end2 and start2 < end1


def generate_work_blocks(total_hours: float, due_date: datetime, existing_events: list):
    """
    Generates non-overlapping work blocks (2-hour sessions) between now and due_date.
    Respects existing calendar events and work window (5pm-9pm).
    Skips days that already have events during the work window.
    """
    blocks = []
    hours_remaining = total_hours
    current_time = datetime.now()
    
    # Round up to nearest hour if needed
    if current_time.minute > 0:
        current_time = current_time.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    
    # Parse existing events into time ranges
    existing_ranges = []
    for event in existing_events:
        start_str = event.get("start", {}).get("dateTime")
        end_str = event.get("end", {}).get("dateTime")
        if start_str and end_str:
            try:
                # Parse ISO format, handling timezone
                if start_str.endswith("Z"):
                    start = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                else:
                    start = datetime.fromisoformat(start_str)
                if end_str.endswith("Z"):
                    end = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
                else:
                    end = datetime.fromisoformat(end_str)
                # Convert to local timezone (naive datetime for comparison)
                if start.tzinfo:
                    start = start.replace(tzinfo=None)
                if end.tzinfo:
                    end = end.replace(tzinfo=None)
                existing_ranges.append((start, end))
            except Exception:
                pass
    
    # Generate blocks day by day, starting from 5pm
    # If current time is before 5pm today, start today at 5pm, otherwise start tomorrow
    if current_time.hour < 17:
        day_start = current_time.replace(hour=17, minute=0, second=0, microsecond=0)
    else:
        # Already past 5pm today, start tomorrow
        day_start = (current_time + timedelta(days=1)).replace(hour=17, minute=0, second=0, microsecond=0)
    
    while hours_remaining > 0 and day_start < due_date:
        # Check if this day has any events during work window (5pm-9pm)
        day_has_events = False
        day_start_check = day_start
        day_end_check = day_start.replace(hour=21, minute=0, second=0, microsecond=0)
        
        for existing_start, existing_end in existing_ranges:
            if time_overlaps(day_start_check, day_end_check, existing_start, existing_end):
                day_has_events = True
                break
        
        # Skip days that already have events during work window
        if day_has_events:
            day_start = (day_start + timedelta(days=1)).replace(hour=17, minute=0, second=0, microsecond=0)
            continue
        
        # Try to schedule a 2-hour block (5pm-7pm or 7pm-9pm)
        block_start = day_start
        block_end = block_start + timedelta(hours=2)
        
        # Check if block is within work window (5pm-9pm)
        if block_start.hour >= 17 and block_end.hour <= 21:
            # Check for conflicts with existing events
            has_conflict = False
            for existing_start, existing_end in existing_ranges:
                if time_overlaps(block_start, block_end, existing_start, existing_end):
                    has_conflict = True
                    break
            
            if not has_conflict:
                blocks.append((block_start, block_end))
                hours_remaining -= 2
                day_start = block_end  # Move to after this block
            else:
                # Shouldn't happen since we checked for day conflicts, but try next slot
                if block_start.hour == 17:
                    # Try 7pm-9pm slot
                    day_start = day_start.replace(hour=19)
                else:
                    # Both slots tried, move to next day
                    day_start = (day_start + timedelta(days=1)).replace(hour=17, minute=0, second=0, microsecond=0)
        else:
            # Outside work window - move to next day
            day_start = (day_start + timedelta(days=1)).replace(hour=17, minute=0, second=0, microsecond=0)
            continue
        
        # If we've scheduled enough, handle remainder
        if hours_remaining <= 0:
            break
        elif hours_remaining < 2:
            # Schedule a shorter final block
            block_start = day_start
            block_end = block_start + timedelta(hours=hours_remaining)
            
            if block_start.hour >= 17 and block_end.hour <= 21:
                has_conflict = False
                for existing_start, existing_end in existing_ranges:
                    if time_overlaps(block_start, block_end, existing_start, existing_end):
                        has_conflict = True
                        break
                
                if not has_conflict:
                    blocks.append((block_start, block_end))
                    hours_remaining = 0
                    break
        
        # If we've tried all slots for the day, move to next day
        if day_start.hour >= 19:
            day_start = (day_start + timedelta(days=1)).replace(hour=17, minute=0, second=0, microsecond=0)
    
    return blocks


while True:
    user_input = input("You: ")

    if user_input.lower() in ["exit", "quit"]:
        typewriter("MARTY: Leaving already? Fine.")
        break

    # PLANNING INTENT DETECTION: Force planning mode for task mentions
    # This happens BEFORE think() - code decides, not LLM
    if not planning_state["active"]:
        planning_keywords = ["due", "deadline", "project", "assignment", "exam"]
        if any(word in user_input.lower() for word in planning_keywords):
            planning_state.update({
                "active": True,
                "task": user_input,
                "due_date": "next week",  # temp placeholder, refine later
                "total_hours": None
            })
            typewriter("MARTY: Roughly how many hours do you think it will take?")
            continue

    # PLANNING MODE: Lock MARTY out, handle state machine in code
    if planning_state["active"]:
        # Check if waiting for final confirmation after preview
        if planning_state.get("waiting_for_final_confirmation"):
            confirmation = classify_confirmation(user_input)
            
            if confirmation == "CONFIRM":
                # Insert all work blocks
                work_blocks = planning_state.get("work_blocks", [])
                task_name = planning_state.get("task", "Work session")
                
                inserted_count = 0
                for start, end in work_blocks:
                    result = add_calendar_event(
                        start_dt=start,
                        end_dt=end,
                        title=task_name,
                        description=f"Work session for: {task_name}"
                    )
                    if "Success" in result:
                        inserted_count += 1
                    else:
                        typewriter(f"MARTY: Warning: Could not add session {start.strftime('%a %-I:%M %p')}: {result}")
                
                if inserted_count > 0:
                    typewriter(f"MARTY: I've added {inserted_count} work session(s) to your calendar. You're all set.")
                else:
                    typewriter("MARTY: I couldn't add any sessions to your calendar. Please check for errors above.")
                planning_state.update({
                    "active": False,
                    "task": None,
                    "due_date": None,
                    "total_hours": None,
                    "work_blocks": None,
                    "waiting_for_final_confirmation": False
                })
                continue
            elif confirmation == "DECLINE":
                typewriter("MARTY: No problem. Let me know if you want to plan it later.")
                planning_state.update({
                    "active": False,
                    "task": None,
                    "due_date": None,
                    "total_hours": None,
                    "work_blocks": None,
                    "waiting_for_final_confirmation": False
                })
                continue
            else:
                typewriter("MARTY: Please answer yes or no. Should I add these to your calendar?")
                continue
        
        # Check if user is responding to calendar confirmation question
        if planning_state["total_hours"] is not None and not planning_state.get("waiting_for_final_confirmation"):
            # User has provided hours, now waiting for confirmation
            confirmation = classify_confirmation(user_input)
            
            if confirmation == "CONFIRM":
                # Read calendar events before scheduling
                try:
                    due_date = parse_due_date(planning_state["due_date"])
                    now = datetime.now()
                    
                    # Fetch existing events
                    existing_events = get_calendar_events_range(now, due_date)
                    
                    # Generate work blocks
                    work_blocks = generate_work_blocks(
                        planning_state["total_hours"],
                        due_date,
                        existing_events
                    )
                    
                    if not work_blocks:
                        typewriter("MARTY: I couldn't find enough free time before the due date. Please free up some time or adjust the deadline.")
                        planning_state.update({
                            "active": False,
                            "task": None,
                            "due_date": None,
                            "total_hours": None
                        })
                        continue
                    
                    # Preview work blocks
                    preview_lines = [f"MARTY: I can schedule {len(work_blocks)} work session(s):"]
                    for i, (start, end) in enumerate(work_blocks, 1):
                        day_name = start.strftime("%a")
                        start_str = start.strftime("%-I:%M %p")
                        end_str = end.strftime("%-I:%M %p")
                        duration = (end - start).total_seconds() / 3600
                        preview_lines.append(f"  {i}. {day_name} {start_str}–{end_str} ({duration:.1f}h)")
                    preview_lines.append("Should I add these to your calendar?")
                    
                    for line in preview_lines:
                        typewriter(line)
                    
                    # Store blocks for final confirmation
                    planning_state["work_blocks"] = work_blocks
                    planning_state["waiting_for_final_confirmation"] = True
                    continue
                    
                except Exception as e:
                    typewriter(f"MARTY: Error scheduling: {e}")
                    planning_state.update({
                        "active": False,
                        "task": None,
                        "due_date": None,
                        "total_hours": None
                    })
                    continue
            elif confirmation == "DECLINE":
                typewriter("MARTY: No problem. Let me know if you want to plan it later.")
                planning_state.update({
                    "active": False,
                    "task": None,
                    "due_date": None,
                    "total_hours": None
                })
                continue
            else:
                # UNKNOWN - ask for clarification
                typewriter("MARTY: Please answer yes or no. Should I add this to your calendar?")
                continue
        
        # User is providing hours
        if planning_state["total_hours"] is None:
            try:
                planning_state["total_hours"] = float(user_input.split()[0])
                blocks = int(planning_state["total_hours"] // 2)
                remainder = planning_state["total_hours"] % 2
                
                summary = f"I'll schedule {blocks} two-hour work sessions"
                if remainder:
                    summary += " and one shorter session"
                summary += f" before {planning_state['due_date']}."
                
                typewriter(f"MARTY: {summary} Should I add this to your calendar?")
            except:
                typewriter("MARTY: Roughly how many hours? A number is fine.")
            continue
        
        # If we get here, planning is active but we don't know what to do
        # This shouldn't happen, but fall through to normal processing
        planning_state.update({"active": False})

    # NORMAL MODE: Let MARTY decide
    result = think(user_input)

    # TOOL REQUEST
    if isinstance(result, dict):
        tool = result.get("tool")
        args = result.get("args", {})

        if tool == "open_app":
            app_key = args.get("app_name", "").lower()

            if app_key in ALLOWED_APPS:
                open_app(ALLOWED_APPS[app_key])
                typewriter(f"MARTY: Opening {ALLOWED_APPS[app_key]}.")
            else:
                typewriter("MARTY: I'm not allowed to open that app.")

        elif tool == "search_web":
            query = args.get("query", "")
            search_web(query)
            typewriter("MARTY: Done.")
        elif tool == "get_today_events":
            events = get_today_events()
            sys.stdout.write("MARTY: Here are today's events: ")
            typewriter(events)
        else:
            typewriter("MARTY: I don't recognize that tool.")

    # NORMAL RESPONSE
    else:
        sys.stdout.write("MARTY: ")
        typewriter(result)
