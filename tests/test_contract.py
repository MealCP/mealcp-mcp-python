"""Contract parity: vendored fixtures must validate against generated models."""

from __future__ import annotations

import json
from pathlib import Path

from mealcp_mcp.models import ErrorEnvelope, PriceHistoryResponse, SearchResponse

CONTRACT = Path(__file__).parent.parent / "contract"


def _load(name: str) -> dict:
    return json.loads((CONTRACT / "fixtures" / f"{name}.json").read_text())


def test_search_response_fixture_validates() -> None:
    model = SearchResponse.model_validate(_load("search_response"))
    assert model.found == len(model.hits)


def test_price_history_fixture_validates() -> None:
    model = PriceHistoryResponse.model_validate(_load("price_history_response"))
    assert model.min_price <= model.avg_price <= model.max_price


def test_error_envelope_fixture_validates() -> None:
    model = ErrorEnvelope.model_validate(_load("error_envelope"))
    assert model.error.code == "service_unavailable"


def test_vendored_spec_matches_generated_models() -> None:
    spec = json.loads((CONTRACT / "openapi.json").read_text())
    schemas = spec["components"]["schemas"]
    assert "SearchResponse" in schemas
    assert "PriceHistoryResponse" in schemas
    assert "ErrorEnvelope" in schemas
