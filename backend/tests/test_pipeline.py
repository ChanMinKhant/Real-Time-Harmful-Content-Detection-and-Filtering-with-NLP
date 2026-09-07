import pytest

from pipeline import CascadingNLPPipeline


@pytest.fixture(scope="module")
def pipeline():
    return CascadingNLPPipeline(cache_size=500)


# ------------------------------------------------------------------ single
@pytest.mark.parametrize("text", [
    "Charles Dickens was a great writer.",
    "the closer of the ceremony",
    "Hello everyone! Have a wonderful day!",
    "you",
    "how are you",
    "are you there",
    "Can you help me with this task?",
    "မင်း",
    "မင်း နေကောင်းလား",
])
def test_benign_texts_not_harmful(pipeline, text):
    assert not pipeline.predict(text)["is_harmful"]


def test_toxic_text_detected_via_tier1(pipeline):
    r = pipeline.predict("you are fucking bastard")
    assert r["is_harmful"]
    assert r["tier_used"].startswith("Tier 1")
    assert r["category"] == "profanity"


def test_repeat_query_uses_cache_tier(pipeline):
    pipeline.predict("totally unique cache probe sentence")
    r = pipeline.predict("totally unique cache probe sentence")
    assert r["tier_used"].startswith("Tier 0")


def test_empty_text(pipeline):
    r = pipeline.predict("   ")
    assert not r["is_harmful"]
    assert "Empty" in r["tier_used"]


def test_result_schema(pipeline):
    r = pipeline.predict("fuck you bitch")
    for key in ("text", "is_harmful", "score", "category", "language", "tier_used", "latency_ms"):
        assert key in r


# ------------------------------------------------------------------- batch
BATCH = [
    {"id": "1", "text": "Good morning teachers and classmates!"},
    {"id": "2", "text": "Go die you pathetic piece of trash."},
    {"id": "3", "text": ""},
    {"id": "4", "text": "What time does the class start tomorrow?"},
]


def test_batch_results_match_individual(pipeline):
    batch = {r["id"]: r for r in pipeline.predict_batch(BATCH)}
    assert len(batch) == 4
    assert not batch["1"]["is_harmful"]
    assert batch["2"]["is_harmful"]
    assert not batch["3"]["is_harmful"] and "Empty" in batch["3"]["tier_used"]
    assert not batch["4"]["is_harmful"]


def test_inbatch_duplicates_share_result(pipeline):
    items = [
        {"id": "x", "text": "in-batch duplicate probe text here"},
        {"id": "y", "text": "in-batch duplicate probe text here"},
    ]
    res = {r["id"]: r for r in pipeline.predict_batch(items)}
    assert res["y"]["tier_used"].startswith("Tier 0")
    assert res["y"]["is_harmful"] == res["x"]["is_harmful"]


# ------------------------------------------------------------------- stats
def test_stats_and_reset(pipeline):
    before = pipeline.get_stats()
    assert before["total_queries"] > 0
    pipeline.reset_stats()
    after = pipeline.get_stats()
    assert after["total_queries"] == 0
    assert after["cache_items_count"] == 0
