from pathlib import Path
from typing import Any

from football_lab.providers.football_data import FootballDataClient


class StubResponse:
    text = '{"teams":[{"id":57,"name":"Arsenal FC"}]}'

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return {"teams": [{"id": 57, "name": "Arsenal FC"}]}


def test_competition_teams_uses_authenticated_endpoint_and_cache(
    tmp_path: Path, monkeypatch
) -> None:
    client = FootballDataClient(api_key="test-token", cache_dir=tmp_path)
    requests: list[tuple[str, dict[str, Any]]] = []

    def get(url: str, **kwargs: Any) -> StubResponse:
        requests.append((url, kwargs))
        return StubResponse()

    monkeypatch.setattr(client.session, "get", get)

    result = client.competition_teams("PL", 2025)
    cached = client.competition_teams("PL", 2025)

    assert result == cached
    assert requests[0][0].endswith("/competitions/PL/teams")
    assert requests[0][1]["params"] == {"season": 2025}
    assert client.session.headers["X-Auth-Token"] == "test-token"
    assert len(requests) == 1
    assert (tmp_path / "PL/2025/teams.json").exists()
