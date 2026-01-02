from brain import think
from tools import open_app, search_web, get_today_events
import sys
import time


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


while True:
    user_input = input("You: ")

    if user_input.lower() in ["exit", "quit"]:
        print("MARTY: Leaving already? Fine.")
        break
    result = think(user_input)

    # TOOL REQUEST
    if isinstance(result, dict):
        tool = result.get("tool")
        args = result.get("args", {})

        if tool == "open_app":
            app_key = args.get("app_name", "").lower()

            if app_key in ALLOWED_APPS:
                open_app(ALLOWED_APPS[app_key])
                print(f"MARTY: Opening {ALLOWED_APPS[app_key]}.")
            else:
                print("MARTY: I’m not allowed to open that app.")

        elif tool == "search_web":
            query = args.get("query", "")
            search_web(query)
            print("MARTY: Done.")
        elif tool == "get_today_events":
            events = get_today_events()
            print("MARTY: Here are today’s events:", events)
        else:
            print("MARTY: I don’t recognize that tool.")

    # NORMAL RESPONSE
    else:
        sys.stdout.write("MARTY: ")
        typewriter(result)
