import pytest

from app import create_app
from app.config import TestingConfig


@pytest.fixture()
def client():
    app = create_app(TestingConfig)
    with app.test_client() as client:
        yield client


def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    body = res.get_json()
    assert body["status"] == "online"
    assert "pipeline_stats" in body
    assert "lexicon_summary" in body


def test_rules_endpoint(client):
    res = client.get("/api/rules")
    assert res.status_code == 200
    body = res.get_json()
    assert "myanmar_lexicon" in body or "lexicon_summary" in body


def test_demo_page_view(client):
    res = client.get("/demo")
    assert res.status_code == 200
    assert "text/html" in res.content_type


def test_analyze_missing_text_returns_400(client):
    res = client.post("/api/analyze", json={})
    assert res.status_code == 400
    assert "error" in res.get_json()


def test_analyze_toxic(client):
    res = client.post("/api/analyze", json={"text": "you are fucking bastard"})
    assert res.status_code == 200
    body = res.get_json()
    assert body["is_harmful"] is True
    assert body["category"] == "profanity"


def test_analyze_benign(client):
    res = client.post("/api/analyze", json={"text": "Charles Dickens was a great writer."})
    assert res.status_code == 200
    body = res.get_json()
    assert body["is_harmful"] is False


def test_analyze_batch_invalid(client):
    res = client.post("/api/analyze-batch", json={"items": "nope"})
    assert res.status_code == 400


def test_analyze_batch_ok(client):
    items = [
        {"id": "a", "text": "Have a wonderful day!"},
        {"id": "b", "text": "fuck you bitch"},
    ]
    res = client.post("/api/analyze-batch", json={"items": items})
    assert res.status_code == 200
    body = res.get_json()
    assert body["batch_size"] == 2
    by_id = {r["id"]: r for r in body["results"]}
    assert not by_id["a"]["is_harmful"]
    assert by_id["b"]["is_harmful"]


def test_reset_stats(client):
    res = client.post("/api/reset-stats")
    assert res.status_code == 200
    stats = client.get("/api/stats").get_json()
    assert stats["total_queries"] == 0
