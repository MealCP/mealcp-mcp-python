"""Constrained query-param types matching the mealcp API's public contract.

These appear as inline query-param schemas in ``contract/openapi.json`` (not
components), so they are hand-maintained here and validated against the spec
on contract updates.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import StringConstraints

CountryCode = Annotated[str, StringConstraints(pattern=r"^[A-Z]{2}$", min_length=2, max_length=2)]
SlugValue = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9_-]+$", max_length=128)]
FreeToken = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9 _-]+$", max_length=128)]

SortOrder = Literal[
    "relevance",
    "newest",
    "oldest",
    "price_asc",
    "price_desc",
    "unit_price_asc",
    "unit_price_desc",
]

__all__ = ["CountryCode", "FreeToken", "SlugValue", "SortOrder"]
