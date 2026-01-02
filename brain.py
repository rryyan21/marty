import requests

OLLAMA_URL = "http://localhost:11434"

SYSTEM_PROMPT = """
You are MARTY — Mostly Accurate, Reasonably Trustworthy, Yet.

Personality:
- Dry
- Lightly sarcastic
- Helpful
- Concise
- JARVIS from iron man

Rules:
- Do NOT mention being an AI model.
- Answer clearly.
- If you are unsure, say so.
"""

def think(user_input: str) -> str:
    """
    Sends user input to Mistral via Ollama and returns MARTY's response.
    """
    payload = {
        "model": "mistral",
        "prompt": f"{SYSTEM_PROMPT}\nUser: {user_input}\nMARTY:",
        "stream": False
    }

    try:
        response = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=60)
        response.raise_for_status()
        return response.json()["response"].strip()

    except requests.exceptions.RequestException as e:
        return f"MARTY: Something went wrong. ({e})"
    