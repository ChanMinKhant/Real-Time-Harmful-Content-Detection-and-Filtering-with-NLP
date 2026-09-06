"""
API Blueprint for Harmful Content Detection NLP Engine.
Provides RESTful endpoints for Chrome Extension, Evaluation Benchmarks, and Demo Clients.
"""

import json
import time
from pathlib import Path
from flask import Blueprint, current_app, jsonify, request

from app.schemas import BatchAnalyzeRequest, SingleAnalyzeRequest, ValidationError
from lexicon_mm import get_lexicon_summary

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.errorhandler(ValidationError)
def handle_validation_error(err: ValidationError):
    return jsonify({"error": err.message}), err.status_code


@api_bp.route("/health", methods=["GET"])
def health():
    """Health check endpoint to verify backend connectivity, uptime, and model stats."""
    pipeline = current_app.nlp_pipeline
    start_time = current_app.config.get("START_TIME", time.time())
    uptime_sec = round(time.time() - start_time, 1)
    
    return jsonify({
        "status": "online",
        "service": "Harmful Content Detection NLP Engine",
        "version": "2.0.0",
        "uptime_seconds": uptime_sec,
        "pipeline_stats": pipeline.get_stats(),
        "lexicon_summary": get_lexicon_summary(),
    }), 200


@api_bp.route("/analyze", methods=["POST"])
def analyze_single():
    """
    Analyzes a single text string.
    Request JSON: { "text": "...", "threshold": 0.6 }
    """
    payload = request.get_json(silent=True)
    req = SingleAnalyzeRequest.from_dict(payload)
    
    pipeline = current_app.nlp_pipeline
    result = pipeline.predict(req.text, sensitivity_threshold=req.threshold)
    return jsonify(result), 200


@api_bp.route("/analyze-batch", methods=["POST"])
def analyze_batch():
    """
    Batch analysis optimized for Chrome Extension DOM sweeping.
    Request JSON: {
        "items": [
            { "id": "el_1", "text": "sample text..." },
            { "id": "el_2", "text": "another text..." }
        ],
        "threshold": 0.6
    }
    """
    payload = request.get_json(silent=True)
    req = BatchAnalyzeRequest.from_dict(payload)
    
    if not req.items:
        return jsonify({
            "batch_size": 0,
            "total_batch_time_ms": 0.0,
            "results": []
        }), 200

    pipeline = current_app.nlp_pipeline
    start_batch = time.perf_counter()
    raw_items = [{"id": item.id, "text": item.text} for item in req.items]
    results = pipeline.predict_batch(raw_items, sensitivity_threshold=req.threshold)
    total_batch_ms = round((time.perf_counter() - start_batch) * 1000.0, 2)

    return jsonify({
        "batch_size": len(results),
        "total_batch_time_ms": total_batch_ms,
        "results": results
    }), 200


@api_bp.route("/stats", methods=["GET"])
def stats():
    """Returns detailed latency, cache hit rate, and throughput stats."""
    pipeline = current_app.nlp_pipeline
    return jsonify(pipeline.get_stats()), 200


@api_bp.route("/reset-stats", methods=["POST"])
def reset_stats():
    """Resets performance statistics counter and clears LRU cache."""
    pipeline = current_app.nlp_pipeline
    pipeline.reset_stats()
    return jsonify({"message": "Stats and Cache successfully reset"}), 200


@api_bp.route("/rules", methods=["GET"])
def get_rules():
    """Serves the active shared rules JSON for client inspection or extension synchronization."""
    rules_path = current_app.config.get("SHARED_RULES_PATH")
    if rules_path and Path(rules_path).exists():
        with open(rules_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data), 200
    
    return jsonify({
        "status": "active",
        "lexicon_summary": get_lexicon_summary()
    }), 200
