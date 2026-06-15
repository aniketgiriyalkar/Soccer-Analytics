from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import requests

from football_lab.config import RAW_DIR


class FootballDataClient:
    """Supplemental adapter for fixtures, tables, and UEFA competition structure."""

    base_url = "https://api.football-data.org/v4"

    def __init__(self, api_key: str | None = None, cache_dir: Path = RAW_DIR / "football-data"):
        self.api_key = api_key or os.getenv("FOOTBALL_DATA_API_KEY")
        self.cache_dir = cache_dir
        self.session = requests.Session()
        if self.api_key:
            self.session.headers["X-Auth-Token"] = self.api_key

    def competition_matches(self, competition_code: str, season: int) -> dict[str, Any]:
        return self._get(
            f"/competitions/{competition_code}/matches",
            {"season": season},
            f"{competition_code}/{season}/matches.json",
        )

    def competition_table(self, competition_code: str, season: int) -> dict[str, Any]:
        return self._get(
            f"/competitions/{competition_code}/standings",
            {"season": season},
            f"{competition_code}/{season}/standings.json",
        )

    def competition_teams(self, competition_code: str, season: int) -> dict[str, Any]:
        return self._get(
            f"/competitions/{competition_code}/teams",
            {"season": season},
            f"{competition_code}/{season}/teams.json",
        )

    def _get(self, path: str, params: dict[str, Any], cache_key: str) -> dict[str, Any]:
        if not self.api_key:
            raise RuntimeError("FOOTBALL_DATA_API_KEY is required for supplemental ingestion")
        destination = self.cache_dir / cache_key
        if destination.exists():
            import json

            return json.loads(destination.read_text(encoding="utf-8"))
        response = self.session.get(f"{self.base_url}{path}", params=params, timeout=30)
        response.raise_for_status()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(response.text, encoding="utf-8")
        return response.json()
