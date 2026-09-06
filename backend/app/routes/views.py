"""
Views Blueprint for serving the Interactive Presentation Demo Feed.
"""

from pathlib import Path
from flask import Blueprint, current_app, Response

views_bp = Blueprint("views", __name__)


@views_bp.route("/", methods=["GET"])
@views_bp.route("/demo", methods=["GET"])
def demo_page():
    """Serves the interactive demo feed directly over HTTP."""
    demo_file = current_app.config.get("DEMO_FILE_PATH")
    if demo_file and Path(demo_file).exists():
        with open(demo_file, "r", encoding="utf-8") as f:
            content = f.read()
        return Response(content, mimetype="text/html; charset=utf-8")
    
    return "Demo HTML presentation file not found.", 404
