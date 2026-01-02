# brain.py
import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"

SYSTEM_PROMPT = """You are MARTY — Mostly Accurate, Reasonably Trustworthy, Yet.

You may either:
- Respond with plain text
- Respond with valid JSON to request a tool

JSON format:
{
  "tool": "<name>",
  "args": { ... }
}

Available tools:
- open_app(app_name: string)
- search_web(query: string)
- get_today_events()

Rules:
- Use JSON ONLY when a tool is needed
- Otherwise respond briefly in text
- Do not add extra commentary
"""

def think(user_input: str):
    payload = {
        "model": "mistral",
        "prompt": f"{SYSTEM_PROMPT}\nUser: {user_input}\nMARTY:",
        "stream": False,
        "max_tokens": 150
    }

    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=60)
        r.raise_for_status()  # Check for HTTP errors
        text = r.json()["response"].strip()

        # Try to parse as JSON (tool call)
        try:
            parsed = json.loads(text)
            # Only treat as tool if it has the expected structure
            if isinstance(parsed, dict) and "tool" in parsed:
                if "args" not in parsed:
                    parsed["args"] = {}
                return parsed

        except json.JSONDecodeError:
            pass  # Not JSON, continue to return as text
        
        return text  # normal reply

    except requests.exceptions.RequestException as e:
        return f"Error: Could not connect to Ollama. ({e})"
    except KeyError:
        return "Error: Unexpected response format from Ollama."