"""Environment-based configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass

API_URL_ENV = "MEALCP_API_URL"
API_KEY_ENV = "MEALCP_API_KEY"
DEFAULT_API_URL = "http://localhost:8000"


@dataclass(frozen=True)
class Settings:
    api_url: str
    api_key: str | None


def get_settings() -> Settings:
    return Settings(
        api_url=os.environ.get(API_URL_ENV, DEFAULT_API_URL).rstrip("/"),
        api_key=os.environ.get(API_KEY_ENV) or None,
    )
