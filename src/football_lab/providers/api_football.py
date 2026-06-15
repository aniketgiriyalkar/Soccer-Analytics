from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import requests

from football_lab.config import RAW_DIR


class ApiFootballClient:
    """Supplemental adapter for current coach metadata from API-Football."""

    base_url = "https://v3.football.api-sports.io"

    def __init__(self, api_key: str | None = None, cache_dir: Path = RAW_DIR / "api-football"):
        self.api_key = api_key or os.getenv("API_FOOTBALL_KEY")
        self.cache_dir = cache_dir
        self.session = requests.Session()
        if self.api_key:
            self.session.headers["x-apisports-key"] = self.api_key

    def league_teams(self, league_id: int, season: int) -> dict[str, Any]:
        return self._get(
            "/teams",
            {"league": league_id, "season": season},
            f"league={league_id}/season={season}/teams.json",
        )

    def team_coaches(self, team_id: int) -> dict[str, Any]:
        return self._get(
            "/coachs",
            {"team": team_id},
            f"team={team_id}/coaches.json",
        )

    def _get(self, path: str, params: dict[str, Any], cache_key: str) -> dict[str, Any]:
        if not self.api_key:
            raise RuntimeError("API_FOOTBALL_KEY is required for API-Football ingestion")
        destination = self.cache_dir / cache_key
        if destination.exists():
            return json.loads(destination.read_text(encoding="utf-8"))
        response = self.session.get(f"{self.base_url}{path}", params=params, timeout=30)
        response.raise_for_status()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(response.text, encoding="utf-8")
        return response.json()
