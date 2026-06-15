import json
from pathlib import Path

import duckdb
import polars as pl

import football_lab.pipeline as pipeline_module
from football_lab.pipeline import Pipeline


def test_rebuild_aggregates_creates_queryable_views(
    tmp_path: Path, monkeypatch
) -> None:
    parquet = tmp_path / "parquet"
    partition = parquet / "competition=premier-league" / "season=2025"
    partition.mkdir(parents=True)
    pl.DataFrame([{"id": "match-1"}]).write_parquet(partition / "matches.parquet")
    monkeypatch.setattr(pipeline_module, "PARQUET_DIR", parquet)

    Pipeline().rebuild_aggregates()

    connection = duckdb.connect(str(parquet / "football_lab.duckdb"))
    try:
        assert connection.execute("SELECT count(*) FROM matches").fetchone() == (1,)
    finally:
        connection.close()


def test_publish_frontend_builds_compact_provider_snapshot(
    tmp_path: Path, monkeypatch
) -> None:
    parquet = tmp_path / "parquet"
    public = tmp_path / "public"
    partition = parquet / "competition=premier-league" / "season=2024"
    partition.mkdir(parents=True)
    public.mkdir()

    pl.DataFrame(
        [
            {
                "id": "player-1",
                "name": "Player One",
                "team": "Arsenal FC",
                "competition_id": "premier-league",
                "season_id": "premier-league-2024",
                "time": 900,
                "goals": 10,
                "key_passes": 20,
                "xg": 8.5,
                "xa": 4.0,
                "position": "F",
            }
        ]
    ).write_parquet(partition / "players.parquet")
    pl.DataFrame(
        [
            {
                "id": "team-1",
                "name": "Arsenal FC",
                "competition_id": "premier-league",
                "season_id": "premier-league-2024",
                "matches": 38,
                "goals": 80,
                "xg": 76.5,
                "xga": 35.5,
                "points": 89,
                "wins": 28,
                "form": [10, 12, 13],
                "ppda_att": 420,
                "ppda_def": 52,
            }
        ]
    ).write_parquet(partition / "teams.parquet")
    pl.DataFrame(
        [
            {
                "id": "manager-1",
                "provider_id": "1",
                "name": "Manager One",
                "team_name": "North London FC",
                "competition_id": "premier-league",
                "season_id": "premier-league-2024",
                "contract_start": "2023-07-01",
                "contract_until": "2027-06-30",
            }
        ]
    ).write_parquet(partition / "managers.parquet")
    pl.DataFrame(
        [
            {
                "id": "match-1",
                "competition_id": "premier-league",
                "season_id": "premier-league-2024",
            }
        ]
    ).write_parquet(partition / "matches.parquet")

    template = {
        "manifest": {
            "schemaVersion": "1.0",
            "dataVersion": "demo",
            "generatedAt": "2026-01-01T00:00:00Z",
            "sourceCommit": "test",
            "status": "demo",
            "disclaimer": "demo",
        },
        "pipeline": {"schedule": "daily", "promotion": "validated", "stages": []},
        "metrics": [],
        "players": [],
        "teams": [],
        "managers": [{"id": "demo"}],
        "shots": [],
        "coverage": [],
    }
    (public / "football-lab.json").write_text(json.dumps(template), encoding="utf-8")

    monkeypatch.setattr(pipeline_module, "PARQUET_DIR", parquet)
    monkeypatch.setattr(pipeline_module, "PUBLIC_DATA_DIR", public)

    Pipeline().publish_frontend()

    published = json.loads((public / "football-lab.json").read_text(encoding="utf-8"))
    snapshot = json.loads((public / "snapshot-manifest.json").read_text(encoding="utf-8"))
    assert published["manifest"]["status"] == "Validated provider snapshot"
    assert published["players"][0]["team"] == "Arsenal FC"
    assert published["players"][0]["metrics"]["goals_per90"] == 1
    assert published["teams"][0]["metrics"]["xg_per_match"] > 2
    assert published["teams"][0]["metrics"]["points_per_match"] > 2
    assert published["teams"][0]["form"] == [10, 12, 13]
    assert published["managers"][0]["club"] == "Arsenal FC"
    assert published["managers"][0]["season"] == "2024/25"
    assert published["managers"][0]["metrics"]["win_pct"] > 70
    assert snapshot["players"] == 1
    assert snapshot["teams"] == 1
    assert snapshot["managers"] == 1


def test_normalize_managers_uses_current_coach_and_canonical_team_name() -> None:
    rows = Pipeline._normalize_managers(
        "premier-league",
        2025,
        [
            {
                "id": 57,
                "name": "North London FC",
                "coach": {
                    "id": 11616,
                    "name": "Mikel Arteta",
                    "contract": {"start": "2019-12-22", "until": "2027-06-30"},
                },
            }
        ],
    )

    assert rows[0]["name"] == "Mikel Arteta"
    assert rows[0]["team_name"] == "Arsenal FC"
    assert Pipeline._team_key(rows[0]["team_name"]) == Pipeline._team_key("Arsenal")


def test_current_api_football_coach_prefers_open_current_spell() -> None:
    selected = Pipeline._current_api_football_coach(
        42,
        [
            {
                "id": 1,
                "name": "Former Coach",
                "career": [{"team": {"id": 42}, "start": "2021-07-01", "end": "2023-06-30"}],
            },
            {
                "id": 2,
                "name": "Current Coach",
                "career": [{"team": {"id": 42}, "start": "2023-07-01", "end": None}],
            },
        ],
    )

    assert selected is not None
    coach, career = selected
    assert coach["name"] == "Current Coach"
    assert career["start"] == "2023-07-01"
