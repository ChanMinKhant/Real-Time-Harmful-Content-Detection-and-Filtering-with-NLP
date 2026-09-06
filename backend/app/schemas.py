"""
Request and Response Schemas and Validation Helpers.
Ensures strong typing, sanitization, and clean error messages without heavy external dependencies.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class ValidationError(Exception):
    """Raised when request payload fails schema validation."""
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


@dataclass
class SingleAnalyzeRequest:
    text: str
    threshold: float = 0.6

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "SingleAnalyzeRequest":
        if data is None or not isinstance(data, dict):
            raise ValidationError("Request body must be a valid JSON object.")
        
        raw_text = data.get("text")
        if raw_text is None or not isinstance(raw_text, str) or not raw_text.strip():
            raise ValidationError("Missing or empty required field 'text'.")

        threshold_raw = data.get("threshold", 0.6)
        try:
            threshold = float(threshold_raw)
            threshold = max(0.0, min(1.0, threshold))
        except (ValueError, TypeError):
            threshold = 0.6

        return cls(text=raw_text.strip(), threshold=threshold)


@dataclass
class BatchItem:
    id: str
    text: str


@dataclass
class BatchAnalyzeRequest:
    items: List[BatchItem] = field(default_factory=list)
    threshold: float = 0.6

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "BatchAnalyzeRequest":
        if data is None or not isinstance(data, dict):
            raise ValidationError("Request body must be a valid JSON object.")
        
        raw_items = data.get("items")
        if raw_items is None or not isinstance(raw_items, list):
            raise ValidationError("Missing or invalid required field 'items' (must be a list).")

        parsed_items: List[BatchItem] = []
        for idx, item in enumerate(raw_items):
            if not isinstance(item, dict):
                raise ValidationError(f"Item at index {idx} must be a JSON object.")
            node_id = str(item.get("id", f"el_{idx}"))
            text = item.get("text", "")
            if not isinstance(text, str):
                text = str(text) if text is not None else ""
            parsed_items.append(BatchItem(id=node_id, text=text))

        threshold_raw = data.get("threshold", 0.6)
        try:
            threshold = float(threshold_raw)
            threshold = max(0.0, min(1.0, threshold))
        except (ValueError, TypeError):
            threshold = 0.6

        return cls(items=parsed_items, threshold=threshold)
