import pytest

from app.schemas import BatchAnalyzeRequest, SingleAnalyzeRequest, ValidationError


def test_single_analyze_valid():
    req = SingleAnalyzeRequest.from_dict({"text": "Hello world", "threshold": 0.75})
    assert req.text == "Hello world"
    assert req.threshold == 0.75


def test_single_analyze_threshold_clamping():
    req1 = SingleAnalyzeRequest.from_dict({"text": "test", "threshold": 1.5})
    assert req1.threshold == 1.0

    req2 = SingleAnalyzeRequest.from_dict({"text": "test", "threshold": -0.5})
    assert req2.threshold == 0.0


def test_single_analyze_missing_text_raises_validation_error():
    with pytest.raises(ValidationError) as exc:
        SingleAnalyzeRequest.from_dict({})
    assert "Missing or empty required field 'text'" in str(exc.value)

    with pytest.raises(ValidationError):
        SingleAnalyzeRequest.from_dict({"text": "   "})


def test_batch_analyze_valid():
    payload = {
        "items": [
            {"id": "1", "text": "Comment 1"},
            {"id": "2", "text": "Comment 2"}
        ],
        "threshold": 0.5
    }
    req = BatchAnalyzeRequest.from_dict(payload)
    assert len(req.items) == 2
    assert req.items[0].id == "1"
    assert req.items[1].text == "Comment 2"
    assert req.threshold == 0.5


def test_batch_analyze_invalid_payload():
    with pytest.raises(ValidationError):
        BatchAnalyzeRequest.from_dict(None)

    with pytest.raises(ValidationError):
        BatchAnalyzeRequest.from_dict({"items": "not a list"})

    with pytest.raises(ValidationError):
        BatchAnalyzeRequest.from_dict({"items": ["not a dict"]})
