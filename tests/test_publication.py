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
                "ppda_att": 420,
                "ppda_def": 52,
            }
        ]
    ).write_parquet(partition / "teams.parquet")
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
    assert published["managers"] == []
    assert snapshot["players"] == 1
    assert snapshot["teams"] == 1
