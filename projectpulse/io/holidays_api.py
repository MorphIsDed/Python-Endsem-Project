"""Public-holiday fetcher with timeout/retry and offline fallback."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import requests

from projectpulse.core.exceptions import HolidayAPIError


class HolidayAPI:
    """Fetch country holidays from the Nager.Date service."""

    def __init__(self, fallback_path: str | Path | None = None):
        self.fallback_path = Path(fallback_path) if fallback_path else None

    def fetch(self, country_code: str, year: int) -> list[date]:
        url = f"https://date.nager.at/api/v3/PublicHolidays/{year}/{country_code.upper()}"
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            payload = response.json()
            return [date.fromisoformat(item["date"]) for item in payload]
        except Exception as exc:
            if self.fallback_path and self.fallback_path.exists():
                data = json.loads(self.fallback_path.read_text(encoding="utf-8"))
                return [date.fromisoformat(item["date"]) for item in data]
            raise HolidayAPIError(f"Unable to fetch holidays for {country_code}: {exc}") from exc
