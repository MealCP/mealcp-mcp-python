"""MCP server tool tests with the HTTP call stubbed (no live API)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx
import pytest
from mcp.server.mcpserver.exceptions import ToolError

from mealcp_mcp.models import PriceHistoryResponse, SearchResponse

FIXTURES = Path(__file__).parent.parent / "contract" / "fixtures"


def _fixture(name: str) -> dict[str, Any]:
    return json.loads((FIXTURES / f"{name}.json").read_text())


def _canned_payload() -> dict[str, Any]:
    return _fixture("search_response")


def _stub_get(
    monkeypatch: pytest.MonkeyPatch,
    *,
    status: int = 200,
    payload: dict[str, Any] | None = None,
) -> None:
    """Replace ``httpx.get`` in the MCP module with a canned responder."""

    def _fake_get(url: str, **_: Any) -> httpx.Response:
        resp = httpx.Response(status, json=payload or {})
        resp.request = httpx.Request("GET", url)
        return resp

    monkeypatch.setattr("mealcp_mcp.server.httpx.get", _fake_get)


def test_tool_returns_search_response(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_get(monkeypatch, payload=_canned_payload())
    from mealcp_mcp.server import search_products

    result = search_products(q="potatoes", country="HU")
    assert isinstance(result, SearchResponse)
    assert result.found == 2
    assert result.query == "potatoes"
    assert [h.id for h in result.hits] == [
        "rp_0f1e2d3c4b5a69788796a5b4c3d2e1f0",
        "rp_1a2b3c4d5e6f708192a3b4c5d6e7f809",
    ]
    assert result.hits[0].latest_unit_price == 599.0
    assert result.facets[0].field == "retailer_slug"


def test_tool_passes_query_params(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def _spy_get(url: str, **kwargs: Any) -> httpx.Response:
        captured["url"] = url
        captured["params"] = kwargs.get("params")
        resp = httpx.Response(200, json=_canned_payload())
        resp.request = httpx.Request("GET", url)
        return resp

    monkeypatch.setattr("mealcp_mcp.server.httpx.get", _spy_get)
    from mealcp_mcp.server import search_products

    search_products(q="krumpli", country="HU", tag="vegan", category="fresh-produce")
    assert captured["url"].endswith("/v1/search")
    assert captured["params"]["q"] == "krumpli"
    assert captured["params"]["country"] == "HU"
    assert captured["params"]["tag"] == "vegan"
    assert captured["params"]["category"] == "fresh-produce"


def test_tool_accepts_leaf_category_slash_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """Leaf slugs are parent-namespaced ("cheese/blue") and must pass through.

    Direct calls bypass MCP input validation, so legality is asserted against
    the generated tool schema (what MCP clients validate with) and the
    constrained param type itself.
    """
    import re

    captured: dict[str, Any] = {}

    def _spy_get(url: str, **kwargs: Any) -> httpx.Response:
        captured["params"] = kwargs.get("params")
        resp = httpx.Response(200, json=_canned_payload())
        resp.request = httpx.Request("GET", url)
        return resp

    monkeypatch.setattr("mealcp_mcp.server.httpx.get", _spy_get)
    from mealcp_mcp.server import mcp, search_products

    search_products(category="cheese/blue")
    assert captured["params"]["category"] == "cheese/blue"

    schema = mcp._tool_manager._tools["search_products"].parameters
    pattern = next(
        sub["pattern"] for sub in schema["properties"]["category"]["anyOf"] if "pattern" in sub
    )
    assert re.fullmatch(pattern, "cheese/blue")
    assert not re.fullmatch(pattern, "cheese//blue")


def test_tool_omits_unset_params(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def _spy_get(url: str, **kwargs: Any) -> httpx.Response:
        captured["params"] = kwargs.get("params")
        resp = httpx.Response(200, json=_canned_payload())
        resp.request = httpx.Request("GET", url)
        return resp

    monkeypatch.setattr("mealcp_mcp.server.httpx.get", _spy_get)
    from mealcp_mcp.server import search_products

    search_products()
    assert captured["params"] == {"q": "", "page": 1, "page_size": 24}


def test_tool_raises_tool_error_when_api_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    error = _fixture("error_envelope")
    _stub_get(monkeypatch, status=error["status"], payload=error)
    from mealcp_mcp.server import search_products

    with pytest.raises(ToolError, match=r"^service_unavailable: index unavailable$"):
        search_products(q="potatoes")


def test_tool_raises_tool_error_without_envelope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stub_get(monkeypatch, status=500, payload={"detail": "boom"})
    from mealcp_mcp.server import search_products

    with pytest.raises(ToolError, match=r"^error: API returned 500"):
        search_products(q="potatoes")


def test_server_registers_both_tools() -> None:
    from mealcp_mcp.server import mcp

    tools = mcp._tool_manager._tools
    assert set(tools) == {"get_price_history", "search_products"}


def _canned_price_history() -> dict[str, Any]:
    return _fixture("price_history_response")


def test_price_history_returns_response(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_get(monkeypatch, payload=_canned_price_history())
    from mealcp_mcp.server import get_price_history

    result = get_price_history("rp_0f1e2d3c4b5a69788796a5b4c3d2e1f0", "2026-01-01", "2026-08-13")
    assert isinstance(result, PriceHistoryResponse)
    assert result.id == "rp_0f1e2d3c4b5a69788796a5b4c3d2e1f0"
    assert result.observation_count == 12
    assert result.change == -50.0
    assert result.last_price == 549.0


def test_price_history_passes_path_and_params(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def _spy_get(url: str, **kwargs: Any) -> httpx.Response:
        captured["url"] = url
        captured["params"] = kwargs.get("params")
        resp = httpx.Response(200, json=_canned_price_history())
        resp.request = httpx.Request("GET", url)
        return resp

    monkeypatch.setattr("mealcp_mcp.server.httpx.get", _spy_get)
    from mealcp_mcp.server import get_price_history

    get_price_history("rp_0f1e2d3c4b5a69788796a5b4c3d2e1f0", "2026-01-01")
    assert captured["url"].endswith("/v1/prices/rp_0f1e2d3c4b5a69788796a5b4c3d2e1f0")
    assert captured["params"] == {"from": "2026-01-01"}


def test_price_history_defaults_to_date(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_get(monkeypatch, payload=_canned_price_history())
    from mealcp_mcp.server import get_price_history

    result = get_price_history("rp_0f1e2d3c4b5a69788796a5b4c3d2e1f0", "2026-01-01")
    assert isinstance(result, PriceHistoryResponse)


def test_price_history_raises_tool_error_when_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stub_get(
        monkeypatch,
        status=404,
        payload={"error": {"code": "not_found", "message": "Product not found"}},
    )
    from mealcp_mcp.server import get_price_history

    with pytest.raises(ToolError, match=r"^not_found: Product not found$"):
        get_price_history("rp_ffffffffffffffffffffffffffffffff", "2026-01-01")
