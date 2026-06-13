from pathlib import Path
from typing import Any

from football_lab.providers.understat import UnderstatClient


class StubResponse:
    def __init__(self, payload: dict[str, Any]):
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return self.payload


def test_league_uses_current_json_endpoint_and_caches_payload(
    tmp_path: Path, monkeypatch
) -> None:
    payload = {
        "dates": [{"id": "1"}],
        "teams": {"1": {"title": "Arsenal FC", "history": []}},
        "players": [{"id": "1", "player_name": "Player"}],
    }
    client = UnderstatClient(request_delay=0, cache_dir=tmp_path)
    requests: list[tuple[str, dict[str, Any]]] = []

    def get(url: str, **kwargs: Any) -> StubResponse:
        requests.append((url, kwargs))
        return StubResponse(payload)

    monkeypatch.setattr(client.session, "get", get)

    result = client.league("premier-league", 2025)
    cached = client.league("premier-league", 2025)

    assert result == cached
    assert result["matches"] == payload["dates"]
    assert requests[0][0].endswith("/getLeagueData/EPL/2025")
    assert requests[0][1]["headers"]["X-Requested-With"] == "XMLHttpRequest"
    assert len(requests) == 1
    assert (tmp_path / "league/premier-league/2025.json").exists()
