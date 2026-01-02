# tools.py
import subprocess
import webbrowser

def open_app(app_name: str):
    subprocess.Popen(["open", "-a", app_name])

def search_web(query: str):
    webbrowser.open(f"https://www.google.com/search?q={query}")
