from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

import requests

from football_lab.config import RAW_DIR, UNDERSTAT_LEAGUES

JSON_PATTERN = re.compile(r"JSON\.parse\('(?P<payload>(?:\\.|[^'])*)'\)")


class UnderstatClient:
    """Small, cached adapter around public Understat pages.

    It does not bypass authentication or technical controls. Cached HTML makes
    backfills resumable and keeps repeated traffic conservative.
    """

    base_url = "https://understat.com"

    def __init__(self, request_delay: float = 1.5, cache_dir: Path = RAW_DIR / "understat"):
        self.request_delay = request_delay
        self.cache_dir = cache_dir
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "FootballLab/1.0 (+https://github.com/aniketgiriyalkar/Soccer-Analytics)"}
        )

    def league(self, league: str, season: int, refresh: bool = False) -> dict[str, Any]:
        if league not in UNDERSTAT_LEAGUES:
            raise ValueError(f"unsupported Understat league: {league}")
        provider_name = UNDERSTAT_LEAGUES[league]
        html = self._get(f"/league/{provider_name}/{season}", f"league/{league}/{season}.html", refresh)
        payloads = self._extract_payloads(html)
        if len(payloads) < 3:
            raise ValueError(f"expected league payloads for {league} {season}, found {len(payloads)}")
        return {"matches": payloads[0], "teams": payloads[1], "players": payloads[2]}

    def match_shots(self, match_id: str, refresh: bool = False) -> dict[str, Any]:
        html = self._get(f"/match/{match_id}", f"match/{match_id}.html", refresh)
        payloads = self._extract_payloads(html)
        if not payloads:
            raise ValueError(f"shot payload missing for match {match_id}")
        return payloads[0]

    def _get(self, path: str, cache_key: str, refresh: bool) -> str:
        destination = self.cache_dir / cache_key
        if destination.exists() and not refresh:
            return destination.read_text(encoding="utf-8")
        response = self.session.get(f"{self.base_url}{path}", timeout=30)
        response.raise_for_status()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(response.text, encoding="utf-8")
        time.sleep(self.request_delay)
        return response.text

    @staticmethod
    def _extract_payloads(html: str) -> list[Any]:
        payloads: list[Any] = []
        for match in JSON_PATTERN.finditer(html):
            encoded = match.group("payload")
            decoded = bytes(encoded, "utf-8").decode("unicode_escape")
            payloads.append(json.loads(decoded))
        return payloads
