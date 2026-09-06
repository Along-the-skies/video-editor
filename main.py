import sys
import threading
import time
import requests
import uvicorn

from frontend.ui import initialize_ui
from backend.server import app


def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")


def wait_for_server():
    for _ in range(50):
        try:
            requests.get("http://127.0.0.1:8000/", timeout=0.5)
            return
        except requests.RequestException:
            time.sleep(0.1)


if __name__ == "__main__":
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    wait_for_server()
    initialize_ui()