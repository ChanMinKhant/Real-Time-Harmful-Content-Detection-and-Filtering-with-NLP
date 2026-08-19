"""
Flask Backend API Server for Real-Time Harmful Content Detection & Element Blurring.
Provides RESTful endpoints for Chrome Extension and Evaluation Clients.
"""

import os
import sys
import time
from flask import Flask, request, jsonify
from flask_cors import CORS

from pipeline import CascadingNLPPipeline

# Initialize Flask App
app = Flask(__name__)
# Enable CORS for all origins (crucial for Chrome Extension content scripts)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Global NLP Pipeline instance
nlp_pipeline = CascadingNLPPipeline(cache_size=3000)
START_TIME = time.time()


@app.route("/", methods=["GET"])
@app.route("/demo", methods=["GET"])
def demo_page():
    """Serves the interactive demo feed directly over HTTP."""
    demo_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "demo", "demo.html")
    if os.path.exists(demo_file):
        with open(demo_file, "r", encoding="utf-8") as f:
            return f.read(), 200, {"Content-Type": "text/html; charset=utf-8"}
    return "Demo file not found", 404


@app.route("/api/health", methods=["GET"])
def health():
    """Health check endpoint to verify backend connectivity and uptime."""
    uptime_sec = round(time.time() - START_TIME, 1)
    stats = nlp_pipeline.get_stats()
    return jsonify({
        "status": "online",
        "service": "Harmful Content Detection NLP Engine",
        "uptime_seconds": uptime_sec,
        "pipeline_stats": stats
    }), 200


@app.route("/api/analyze", methods=["POST"])
def analyze_single():
    """
    Analyzes a single text string.
    Request JSON: { "text": "...", "threshold": 0.6 }
    """
    data = request.get_json(silent=True) or {}
    text = data.get("text", "")
    threshold = float(data.get("threshold", 0.6))
    
    if not text:
        return jsonify({"error": "Missing 'text' in request body"}), 400

    result = nlp_pipeline.predict(text, sensitivity_threshold=threshold)
    return jsonify(result), 200


@app.route("/api/analyze-batch", methods=["POST"])
def analyze_batch():
    """
    Batch analysis for Chrome Extension DOM sweeping.
    Request JSON: {
        "items": [
            { "id": "el_1", "text": "sample text..." },
            { "id": "el_2", "text": "another text..." }
        ],
        "threshold": 0.6
    }
    """
    data = request.get_json(silent=True) or {}
    items = data.get("items", [])
    threshold = float(data.get("threshold", 0.6))

    if not items or not isinstance(items, list):
        return jsonify({"error": "Missing or invalid 'items' list"}), 400

    start_batch = time.perf_counter()
    results = nlp_pipeline.predict_batch(items, sensitivity_threshold=threshold)
    total_batch_ms = round((time.perf_counter() - start_batch) * 1000.0, 2)

    return jsonify({
        "batch_size": len(results),
        "total_batch_time_ms": total_batch_ms,
        "results": results
    }), 200


@app.route("/api/stats", methods=["GET"])
def stats():
    """Returns detailed latency, cache hit rate, and throughput stats."""
    return jsonify(nlp_pipeline.get_stats()), 200


@app.route("/api/reset-stats", methods=["POST"])
def reset_stats():
    """Resets performance statistics counter."""
    nlp_pipeline.stats = {
        "total_queries": 0,
        "tier0_cache_hits": 0,
        "tier1_lexicon_hits": 0,
        "tier2_ml_hits": 0,
        "tier3_transformer_hits": 0,
        "avg_latency_ms": 0.0,
        "total_latency_ms": 0.0
    }
    nlp_pipeline.cache.clear()
    return jsonify({"message": "Stats and Cache successfully reset"}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    if "PORT" not in os.environ:
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                if s.connect_ex(('127.0.0.1', port)) == 0:
                    print(f"⚠️ Port {port} is currently in use (e.g. macOS AirPlay). Switching to fallback port 5001...")
                    port = 5001
        except Exception:
            pass

    print(f"\n=======================================================")
    print(f"🛡️  Harmful Content NLP Backend (Flask) Running on http://127.0.0.1:{port}")
    print(f"📡  Ready to accept requests from Chrome Extension...")
    print(f"=======================================================\n")
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
