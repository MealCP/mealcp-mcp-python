"""MCP server exposing the mealcp product search and price history as tools.

Each tool is a thin HTTP client over the mealcp API's public endpoints
(``GET /v1/search``, ``GET /v1/prices/{product_id}``), configured solely via
the ``MEALCP_API_URL`` and ``MEALCP_API_KEY`` environment variables.
"""

from __future__ import annotations

import httpx
from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from mealcp_mcp.config import get_settings
from mealcp_mcp.models import PriceHistoryResponse, SearchResponse
from mealcp_mcp.param_types import CountryCode, FreeToken, SlugValue, SortOrder

mcp = MCPServer("mealcp")


def _tool_error(resp: httpx.Response) -> ToolError:
    """Translate a non-2xx API response into a ToolError via the error envelope.

    Message format is ``"<code>: <message>"`` (see the API's ``ErrorEnvelope``)
    so MCP consumers can branch on the stable token.
    """
    try:
        error = resp.json()["error"]
        return ToolError(f"{error['code']}: {error['message']}")
    except (ValueError, KeyError):
        return ToolError(f"error: API returned {resp.status_code} with no error envelope")


@mcp.tool()
def search_products(
    q: str = "",
    country: CountryCode | None = None,
    retailer: SlugValue | None = None,
    chain: SlugValue | None = None,
    brand: FreeToken | None = None,
    tag: SlugValue | None = None,
    category: SlugValue | None = None,
    city: FreeToken | None = None,
    currency: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    sort: SortOrder | None = None,
    page: int = 1,
    page_size: int = 24,
) -> SearchResponse:
    """Search the grocery product catalog by keyword with faceted filtering.

    Returns matching products with name, brand, price, unit price, retailer and
    a URL, plus facet counts for retailers, brands and countries.

    Args:
        q: Free-text query (e.g. "potatoes", "krumpli"). Empty returns all,
            sorted by ``sort`` or recency.
        country: ISO 3166-1 alpha-2 country code (e.g. HU, FR).
        retailer: Retailer slug (e.g. tesco-hu, auchan-fr).
        chain: Chain slug (e.g. tesco, auchan).
        brand: Brand free-text token.
        tag: Tag slug (e.g. vegan).
        category: Category slug at any level (L1/L2/L3, e.g. fresh-produce,
            dairy-eggs, vegetables/potatoes); matches the whole subtree.
        city: City free-text token filtering stores carrying the product.
        currency: ISO 4217 currency code (e.g. HUF, EUR).
        min_price: Minimum latest price (inclusive).
        max_price: Maximum latest price (inclusive).
        sort: Stable sort token: relevance, newest, oldest, price_asc,
            price_desc, unit_price_asc, unit_price_desc.
        page: 1-indexed result page.
        page_size: Hits per page (1-100).

    Returns:
        A structured search response.

    Raises:
        mcp.server.mcpserver.exceptions.ToolError: If the search API is
            unavailable; the message starts with the API's stable error token.
    """
    params: dict[str, str | int | float] = {
        k: v
        for k, v in {
            "q": q,
            "country": country,
            "retailer": retailer,
            "chain": chain,
            "brand": brand,
            "tag": tag,
            "category": category,
            "city": city,
            "currency": currency,
            "min_price": min_price,
            "max_price": max_price,
            "sort": sort,
            "page": page,
            "page_size": page_size,
        }.items()
        if v is not None
    }
    settings = get_settings()
    headers = {"X-API-Key": settings.api_key} if settings.api_key else None
    try:
        resp = httpx.get(
            f"{settings.api_url}/v1/search", params=params, headers=headers, timeout=10.0
        )
        resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise _tool_error(exc.response) from exc
    except httpx.HTTPError as exc:
        raise ToolError(f"service_unavailable: {exc}") from exc
    return SearchResponse.model_validate(resp.json())


@mcp.tool()
def get_price_history(
    product_id: str,
    from_date: str,
    to_date: str | None = None,
) -> PriceHistoryResponse:
    """Get aggregated price-history stats for one product over a date range.

    Returns min/max/avg/first/last price plus the net change over the window,
    pooled across every store carrying the product. Pair with ``search_products``
    first and pass a hit's ``id`` here verbatim.

    Args:
        product_id: Opaque product id from a search hit (e.g.
            ``rp_550e8400e29b41d4a8b2c3d1e9f7a6c8``).
        from_date: ISO date, inclusive lower bound (e.g. "2026-01-01").
        to_date: ISO date, inclusive upper bound; defaults to today.

    Returns:
        Aggregated price-history stats.

    Raises:
        mcp.server.mcpserver.exceptions.ToolError: If the API is unavailable
            or the product is not found; the message starts with the API's
            stable error token.
    """
    params: dict[str, str] = {"from": from_date}
    if to_date is not None:
        params["to"] = to_date
    settings = get_settings()
    headers = {"X-API-Key": settings.api_key} if settings.api_key else None
    try:
        resp = httpx.get(
            f"{settings.api_url}/v1/prices/{product_id}",
            params=params,
            headers=headers,
            timeout=10.0,
        )
        resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise _tool_error(exc.response) from exc
    except httpx.HTTPError as exc:
        raise ToolError(f"service_unavailable: {exc}") from exc
    return PriceHistoryResponse.model_validate(resp.json())


__all__ = ["get_price_history", "mcp", "search_products"]
