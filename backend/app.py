"""
Entry point for the Harmful Content Detection NLP Backend Server.
Provides RESTful APIs for Chrome Extension and Presentation Clients.
"""

import os
import socket
import sys

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

app = create_app()


def is_port_in_use(host: str, port: int) -> bool:
    """Checks if a network port is already occupied."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            return s.connect_ex((host, port)) == 0
    except Exception:
        return False


if __name__ == "__main__":
    host = os.environ.get("HOST", app.config.get("HOST", "127.0.0.1"))
    port = int(os.environ.get("PORT", app.config.get("PORT", 5000)))

    # Gracefully switch to fallback port 5001 if 5000 is occupied (e.g. macOS AirPlay)
    if "PORT" not in os.environ and is_port_in_use(host, port):
        print(f"⚠️ Port {port} is currently in use (e.g. macOS AirPlay). Switching to fallback port 5001...")
        port = 5001

    print(f"\n=======================================================")
    print(f"🛡️  Harmful Content NLP Backend (Flask) Running on http://{host}:{port}")
    print(f"📡  Ready to accept requests from Chrome Extension...")
    print(f"=======================================================\n")
    app.run(host=host, port=port, debug=False, threaded=True)
