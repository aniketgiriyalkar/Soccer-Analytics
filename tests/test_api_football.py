from pathlib import Path
from typing import Any

from football_lab.providers.api_football import ApiFootballClient


class StubResponse:
    text = '{"response":[{"team":{"id":42,"name":"Arsenal"}}]}'

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return {"response": [{"team": {"id": 42, "name": "Arsenal"}}]}


def test_league_teams_uses_api_sports_header_and_cache(
    tmp_path: Path, monkeypatch
) -> None:
    client = ApiFootballClient(api_key="test-token", cache_dir=tmp_path)
    requests: list[tuple[str, dict[str, Any]]] = []

    def get(url: str, **kwargs: Any) -> StubResponse:
        requests.append((url, kwargs))
        return StubResponse()

    monkeypatch.setattr(client.session, "get", get)

    result = client.league_teams(39, 2025)
    cached = client.league_teams(39, 2025)

    assert result == cached
    assert requests[0][0].endswith("/teams")
    assert requests[0][1]["params"] == {"league": 39, "season": 2025}
    assert client.session.headers["x-apisports-key"] == "test-token"
    assert len(requests) == 1
    assert (tmp_path / "league=39/season=2025/teams.json").exists()
