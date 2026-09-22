"""Parse and validate Ollama JSON responses."""

from __future__ import annotations

import json
import re

from pydantic import ValidationError

from src.storage.models import CryptoAnalysisResult

_JSON_BLOCK = re.compile(r"\{[\s\S]*\}")


def validate_analysis_json(data: dict) -> CryptoAnalysisResult:
    return CryptoAnalysisResult.model_validate(data)


def parse_analysis_response(raw: str, headline_id: str) -> CryptoAnalysisResult | None:
    text = raw.strip()
    if not text:
        return None
    try:
        payload = json.loads(text)
        return validate_analysis_json(payload)
    except json.JSONDecodeError:
        match = _JSON_BLOCK.search(text)
        if not match:
            return None
        try:
            payload = json.loads(match.group(0))
            payload.setdefault("headline_id", headline_id)
            return validate_analysis_json(payload)
        except (json.JSONDecodeError, ValidationError):
            return None
    except ValidationError:
        return None
