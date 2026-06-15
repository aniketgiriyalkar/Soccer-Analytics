from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import unicodedata
from datetime import UTC, datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import polars as pl

from football_lab.config import (
    API_FOOTBALL_LEAGUES,
    CHECKPOINT_DIR,
    DISPLAY_NAMES,
    FOOTBALL_DATA_COMPETITIONS,
    PARQUET_DIR,
    PUBLIC_DATA_DIR,
    Settings,
)
from football_lab.metrics import per_90, percentile_rank
from football_lab.models import CoverageLevel, MetricCoverage
from football_lab.providers.api_football import ApiFootballClient
from football_lab.providers.football_data import FootballDataClient
from football_lab.providers.understat import UnderstatClient


class Pipeline:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()
        self.understat = UnderstatClient(request_delay=self.settings.request_delay)
        self.football_data = FootballDataClient()
        self.api_football = ApiFootballClient()

    def backfill(self, league: str, from_season: int, to_season: int, include_shots: bool) -> None:
        if from_season > to_season:
            raise ValueError("from_season must be before or equal to to_season")
        for season in range(from_season, to_season + 1):
            self.ingest_understat_season(league, season, include_shots)

    def ingest_understat_season(self, league: str, season: int, include_shots: bool = False) -> None:
        payload = self.understat.league(league, season)
        season_id = f"{league}-{season}"
        destination = PARQUET_DIR / f"competition={league}" / f"season={season}"
        destination.mkdir(parents=True, exist_ok=True)

        matches = [self._normalize_match(league, season, row) for row in payload["matches"]]
        players = [self._normalize_player(league, season, row) for row in payload["players"]]
        teams = self._normalize_teams(league, season, payload["teams"])
        self._write_parquet(destination / "matches.parquet", matches)
        self._write_parquet(destination / "players.parquet", players)
        self._write_parquet(destination / "teams.parquet", teams)

        shot_rows: list[dict[str, Any]] = []
        if include_shots:
            for match in matches:
                raw_shots = self.understat.match_shots(match["provider_id"])
                shot_rows.extend(self._normalize_shots(match, raw_shots))
            self._write_parquet(destination / "shots.parquet", shot_rows)

        coverage = MetricCoverage(
            competition_id=league,
            season_id=season_id,
            standard_stats=CoverageLevel.PARTIAL,
            xg=CoverageLevel.COMPLETE,
            events=CoverageLevel.PARTIAL if include_shots else CoverageLevel.UNAVAILABLE,
            ingested_matches=len(matches),
            generated_at=datetime.now(UTC),
        )
        checkpoint = {
            "coverage": coverage.model_dump(mode="json"),
            "hash": self._content_hash({"matches": matches, "players": players, "teams": teams}),
        }
        self._write_json(CHECKPOINT_DIR / f"{season_id}.json", checkpoint)

    def ingest_current_managers(self, league: str, season: int) -> bool:
        """Store current coach assignments without making the core refresh provider-dependent."""
        rows: list[dict[str, Any]] = []
        if not self.football_data.api_key:
            print(
                "Skipping manager refresh: FOOTBALL_DATA_API_KEY is not configured.",
                file=sys.stderr,
            )
        else:
            competition_code = FOOTBALL_DATA_COMPETITIONS[league]
            try:
                payload = self.football_data.competition_teams(competition_code, season)
                rows = self._normalize_managers(league, season, payload.get("teams", []))
            except Exception as exc:
                print(
                    f"Manager refresh unavailable for {league}: {type(exc).__name__}: {exc}",
                    file=sys.stderr,
                )

        if not rows:
            print(
                f"No current coaches returned for {league} from football-data.org.",
                file=sys.stderr,
            )
            rows = self._api_football_manager_rows(league, season)
        if not rows:
            print(f"No current coaches returned for {league} from supplemental feeds.", file=sys.stderr)
            return False

        destination = PARQUET_DIR / f"competition={league}" / f"season={season}"
        destination.mkdir(parents=True, exist_ok=True)
        self._write_parquet(destination / "managers.parquet", rows)
        return True

    def _api_football_manager_rows(self, league: str, season: int) -> list[dict[str, Any]]:
        if not self.api_football.api_key:
            print("Skipping API-Football manager fallback: API_FOOTBALL_KEY is not configured.", file=sys.stderr)
            return []
        destination = PARQUET_DIR / f"competition={league}" / f"season={season}"
        team_file = destination / "teams.parquet"
        if not team_file.exists():
            return []
        target_teams = pl.read_parquet(team_file).to_dicts()
        league_id = API_FOOTBALL_LEAGUES[league]
        try:
            teams_payload = self.api_football.league_teams(league_id, season)
        except Exception as exc:
            print(
                f"API-Football teams unavailable for {league}: {type(exc).__name__}: {exc}",
                file=sys.stderr,
            )
            return []

        rows: list[dict[str, Any]] = []
        for item in teams_payload.get("response", []):
            team = item.get("team") or {}
            api_team_id = team.get("id")
            team_name = str(team.get("name") or "").strip()
            if not api_team_id or not team_name:
                continue
            matched_team = self._find_team(target_teams, league, f"{league}-{season}", team_name)
            if not matched_team:
                continue
            try:
                coaches_payload = self.api_football.team_coaches(int(api_team_id))
            except Exception as exc:
                print(
                    f"API-Football coach unavailable for {team_name}: {type(exc).__name__}: {exc}",
                    file=sys.stderr,
                )
                continue
            coach_record = self._current_api_football_coach(int(api_team_id), coaches_payload.get("response", []))
            if not coach_record:
                continue
            coach, career = coach_record
            provider_id = str(coach.get("id") or self._team_key(str(coach.get("name") or "")))
            rows.append(
                {
                    "id": f"api-football-manager-{provider_id}-{league}-{season}",
                    "provider_id": provider_id,
                    "name": str(coach.get("name") or "").strip(),
                    "team_name": self._canonical_team_name(matched_team["name"]),
                    "competition_id": league,
                    "season_id": f"{league}-{season}",
                    "contract_start": career.get("start"),
                    "contract_until": career.get("end"),
                }
            )
        return rows

    def rebuild_aggregates(self) -> None:
        """Build a queryable DuckDB database from all available Parquet partitions."""
        import duckdb

        PARQUET_DIR.mkdir(parents=True, exist_ok=True)
        database = PARQUET_DIR / "football_lab.duckdb"
        connection = duckdb.connect(str(database))
        for entity in ("matches", "players", "teams", "managers", "shots"):
            pattern = str(PARQUET_DIR / "competition=*" / "season=*" / f"{entity}.parquet")
            files = list(PARQUET_DIR.glob(f"competition=*/season=*/{entity}.parquet"))
            if files:
                escaped_pattern = pattern.replace("'", "''")
                connection.execute(
                    f"CREATE OR REPLACE VIEW {entity} "
                    f"AS SELECT * FROM read_parquet('{escaped_pattern}')"
                )
        connection.close()

    def audit_coverage(self) -> list[dict[str, Any]]:
        audits: list[dict[str, Any]] = []
        for checkpoint in sorted(CHECKPOINT_DIR.glob("*.json")):
            record = json.loads(checkpoint.read_text(encoding="utf-8"))
            coverage = record["coverage"]
            expected = coverage.get("expected_matches")
            ingested = coverage["ingested_matches"]
            audits.append(
                {
                    "season_id": coverage["season_id"],
                    "ingested_matches": ingested,
                    "expected_matches": expected,
                    "status": "complete" if expected and expected == ingested else "needs-review",
                }
            )
        return audits

    def publish_frontend(self) -> None:
        """Publish compact, validated JSON from the available Parquet partitions."""
        player_files = sorted(PARQUET_DIR.glob("competition=*/season=*/players.parquet"))
        team_files = sorted(PARQUET_DIR.glob("competition=*/season=*/teams.parquet"))
        manager_files = sorted(PARQUET_DIR.glob("competition=*/season=*/managers.parquet"))
        match_files = sorted(PARQUET_DIR.glob("competition=*/season=*/matches.parquet"))
        if not player_files or not team_files or not match_files:
            raise RuntimeError("no normalized Parquet data is available to publish")

        template_path = PUBLIC_DATA_DIR / "football-lab.json"
        template = json.loads(template_path.read_text(encoding="utf-8"))
        players_frame = pl.concat([pl.read_parquet(path) for path in player_files], how="diagonal")
        teams_frame = pl.concat([pl.read_parquet(path) for path in team_files], how="diagonal")
        managers_frame = (
            pl.concat([pl.read_parquet(path) for path in manager_files], how="diagonal")
            if manager_files
            else pl.DataFrame()
        )
        matches_frame = pl.concat([pl.read_parquet(path) for path in match_files], how="diagonal")

        players = self._publish_players(players_frame)
        teams = self._publish_teams(teams_frame)
        managers = self._publish_managers(managers_frame, teams_frame)
        coverage = self._publish_coverage(matches_frame)
        shots = self._publish_shots()
        generated_at = datetime.now(UTC)
        digest = self._content_hash(
            {
                "players": players,
                "teams": teams,
                "managers": managers,
                "shots": shots,
                "coverage": coverage,
            }
        )[:12]

        template["manifest"].update(
            {
                "dataVersion": f"{generated_at:%Y.%m.%d}-{digest}",
                "generatedAt": generated_at.isoformat().replace("+00:00", "Z"),
                "sourceCommit": self._source_commit(),
                "status": "Validated provider snapshot",
                "disclaimer": (
                    "Provider-backed snapshot generated by the scheduled Football Lab pipeline. "
                    "Metric availability varies by competition and season and is disclosed in Coverage."
                ),
            }
        )
        template["players"] = players
        template["teams"] = teams
        template["managers"] = managers
        template["shots"] = shots
        template["coverage"] = coverage
        self._write_json(template_path, template)
        self._write_json(
            PUBLIC_DATA_DIR / "snapshot-manifest.json",
            {
                "schemaVersion": self.settings.schema_version,
                "dataVersion": template["manifest"]["dataVersion"],
                "generatedAt": template["manifest"]["generatedAt"],
                "players": len(players),
                "teams": len(teams),
                "managers": len(managers),
                "shots": len(shots),
                "coverageRecords": len(coverage),
                "partitions": {
                    "players": len(player_files),
                    "teams": len(team_files),
                    "managers": len(manager_files),
                    "matches": len(match_files),
                },
            },
        )

    def export_schema(self) -> None:
        from football_lab.models import Match, MatchEvent, ManagerTenure, MetricCoverage, Player, Shot, Team

        schema = {
            model.__name__: model.model_json_schema()
            for model in (Match, MatchEvent, ManagerTenure, MetricCoverage, Player, Shot, Team)
        }
        self._write_json(PUBLIC_DATA_DIR / "schema.json", schema)

    @staticmethod
    def _publish_players(frame: pl.DataFrame) -> list[dict[str, Any]]:
        rows = frame.filter(pl.col("time") >= 450).to_dicts()
        metric_population: dict[tuple[str, str], list[float]] = {}
        calculated: list[dict[str, Any]] = []
        for row in rows:
            minutes = int(row.get("time") or 0)
            position = Pipeline._position_group(str(row.get("position") or ""))
            metrics = {
                "goals_per90": per_90(float(row.get("goals") or 0), minutes) or 0,
                "xg_per90": per_90(float(row.get("xg") or 0), minutes) or 0,
                "xa_per90": per_90(float(row.get("xa") or 0), minutes) or 0,
                "key_passes_per90": per_90(float(row.get("key_passes") or 0), minutes) or 0,
                "progressive_actions_per90": 0.0,
                "duel_win_pct": 0.0,
                "recoveries_per90": 0.0,
                "cards_per90": 0.0,
                "restart_delay_seconds": 0.0,
                "save_pct": 0.0,
            }
            record = {
                "id": row["id"],
                "name": row["name"],
                "team": row.get("team") or "Unknown team",
                "competition": DISPLAY_NAMES[row["competition_id"]],
                "season": Pipeline._season_label(row["season_id"]),
                "position": position,
                "age": 0,
                "minutes": minutes,
                "metrics": {key: round(value, 4) for key, value in metrics.items()},
                "percentiles": {},
            }
            calculated.append(record)
            for key in ("goals_per90", "xg_per90", "xa_per90", "key_passes_per90"):
                metric_population.setdefault((position, key), []).append(metrics[key])

        for record in calculated:
            for key in record["metrics"]:
                population = metric_population.get((record["position"], key))
                record["percentiles"][key] = (
                    percentile_rank(record["metrics"][key], population) if population else 0
                )
        return sorted(calculated, key=lambda row: (-row["minutes"], row["name"]))

    @staticmethod
    def _publish_teams(frame: pl.DataFrame) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for row in frame.to_dicts():
            matches = int(row.get("matches") or 0)
            ppda_def = float(row.get("ppda_def") or 0)
            ppda_att = float(row.get("ppda_att") or 0)
            records.append(
                {
                    "id": row["id"],
                    "name": row["name"],
                    "competition": DISPLAY_NAMES[row["competition_id"]],
                    "season": Pipeline._season_label(row["season_id"]),
                    "matches": matches,
                    "metrics": {
                        "goals_per_match": round(float(row.get("goals") or 0) / matches, 4)
                        if matches
                        else 0,
                        "xg_per_match": round(float(row.get("xg") or 0) / matches, 4)
                        if matches
                        else 0,
                        "points_per_match": round(float(row.get("points") or 0) / matches, 4)
                        if matches
                        else 0,
                        "xg_difference_per_match": round(
                            (float(row.get("xg") or 0) - float(row.get("xga") or 0)) / matches,
                            4,
                        )
                        if matches
                        else 0,
                        "win_pct": round(float(row.get("wins") or 0) / matches * 100, 2)
                        if matches
                        else 0,
                        "shots_per_match": 0,
                        "possession_pct": 0,
                        "progressive_actions": 0,
                        "ppda": round(ppda_att / ppda_def, 4) if ppda_def else 0,
                        "cards_per_match": 0,
                        "restart_delay_seconds": 0,
                    },
                    "form": row.get("form") or [],
                }
            )
        return sorted(records, key=lambda row: (row["competition"], row["name"]))

    @staticmethod
    def _publish_managers(
        managers_frame: pl.DataFrame, teams_frame: pl.DataFrame
    ) -> list[dict[str, Any]]:
        if managers_frame.is_empty():
            return []

        team_rows = teams_frame.to_dicts()
        records: list[dict[str, Any]] = []
        for row in managers_frame.to_dicts():
            team = Pipeline._find_team(
                team_rows,
                row["competition_id"],
                row["season_id"],
                row["team_name"],
            )
            if not team:
                continue
            matches = int(team.get("matches") or 0)
            if not matches:
                continue
            xg = float(team.get("xg") or 0)
            xga = float(team.get("xga") or 0)
            contract_start = row.get("contract_start")
            contract_until = row.get("contract_until")
            tenure = Pipeline._manager_tenure_label(contract_start, contract_until)
            records.append(
                {
                    "id": row["id"],
                    "name": row["name"],
                    "club": team["name"],
                    "competition": DISPLAY_NAMES[row["competition_id"]],
                    "season": Pipeline._season_label(row["season_id"]),
                    "tenure": tenure,
                    "matches": matches,
                    "sampleLabel": "Club season sample under the current listed coach",
                    "metrics": {
                        "points_per_game": round(float(team.get("points") or 0) / matches, 4),
                        "xg_difference_per90": round((xg - xga) / matches, 4),
                        "win_pct": round(float(team.get("wins") or 0) / matches * 100, 2),
                        "goals_per_match": round(float(team.get("goals") or 0) / matches, 4),
                        "xg_per_match": round(xg / matches, 4),
                        "ppda": round(
                            float(team.get("ppda_att") or 0)
                            / float(team.get("ppda_def") or 1),
                            4,
                        ),
                    },
                }
            )
        return sorted(records, key=lambda row: (row["competition"], row["club"]))

    @staticmethod
    def _publish_coverage(frame: pl.DataFrame) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for row in frame.group_by(["competition_id", "season_id"]).len().sort(
            ["season_id", "competition_id"], descending=[True, False]
        ).to_dicts():
            season = row["season_id"].rsplit("-", 1)[-1]
            has_shots = bool(
                list(
                    PARQUET_DIR.glob(
                        f"competition={row['competition_id']}/season={season}/shots.parquet"
                    )
                )
            )
            records.append(
                {
                    "competition": DISPLAY_NAMES[row["competition_id"]],
                    "season": Pipeline._season_label(row["season_id"]),
                    "standardStats": "partial",
                    "xg": "complete",
                    "events": "partial" if has_shots else "unavailable",
                }
            )
        return records

    @staticmethod
    def _publish_shots() -> list[dict[str, Any]]:
        shot_files = sorted(PARQUET_DIR.glob("competition=*/season=*/shots.parquet"))
        if not shot_files:
            return []
        frame = pl.concat([pl.read_parquet(path) for path in shot_files], how="diagonal")
        latest_match = frame.select(pl.col("match_id").last()).item()
        rows = frame.filter(pl.col("match_id") == latest_match).to_dicts()
        return [
            {
                "id": row["id"],
                "player": row.get("player") or "Unknown player",
                "team": row.get("team") or row["team_id"],
                "minute": row["minute"],
                "x": row["x"],
                "y": row["y"],
                "xg": row["xg"],
                "result": Pipeline._shot_result(row["result"]),
                "situation": row.get("situation") or "Unknown",
            }
            for row in rows
        ]

    @staticmethod
    def _position_group(value: str) -> str:
        primary = value.split()[0].upper() if value else ""
        return {
            "GK": "Goalkeeper",
            "D": "Centre-back",
            "M": "Central midfield",
            "F": "Striker",
            "S": "Striker",
        }.get(primary, "Central midfield")

    @staticmethod
    def _season_label(season_id: str) -> str:
        start = int(season_id.rsplit("-", 1)[-1])
        return f"{start}/{str(start + 1)[-2:]}"

    @staticmethod
    def _shot_result(value: str) -> str:
        return {
            "Goal": "Goal",
            "SavedShot": "Saved",
            "BlockedShot": "Blocked",
            "MissedShots": "Missed",
            "ShotOnPost": "Missed",
        }.get(value, "Missed")

    @staticmethod
    def _normalize_match(league: str, season: int, row: dict[str, Any]) -> dict[str, Any]:
        home = row["h"]
        away = row["a"]
        return {
            "id": f"understat-match-{row['id']}",
            "provider_id": str(row["id"]),
            "competition_id": league,
            "competition": DISPLAY_NAMES[league],
            "season_id": f"{league}-{season}",
            "season": f"{season}/{str(season + 1)[-2:]}",
            "home_team_id": f"understat-team-{home['id']}",
            "away_team_id": f"understat-team-{away['id']}",
            "kickoff": row["datetime"],
            "home_goals": row.get("goals", {}).get("h"),
            "away_goals": row.get("goals", {}).get("a"),
            "home_xg": row.get("xG", {}).get("h"),
            "away_xg": row.get("xG", {}).get("a"),
        }

    @staticmethod
    def _normalize_player(league: str, season: int, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": f"understat-player-{row['id']}",
            "provider_id": str(row["id"]),
            "name": row["player_name"],
            "team": row.get("team_title"),
            "competition_id": league,
            "season_id": f"{league}-{season}",
            "games": int(row.get("games", 0)),
            "time": int(row.get("time", 0)),
            "goals": int(row.get("goals", 0)),
            "assists": int(row.get("assists", 0)),
            "shots": int(row.get("shots", 0)),
            "key_passes": int(row.get("key_passes", 0)),
            "xg": float(row.get("xG", 0)),
            "npxg": float(row.get("npxG", 0)),
            "xa": float(row.get("xA", 0)),
            "position": row.get("position"),
        }

    @staticmethod
    def _normalize_teams(league: str, season: int, rows: dict[str, Any]) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for provider_id, team in rows.items():
            history = team.get("history", [])
            points = [int(row.get("pts", 0)) for row in history]
            normalized.append(
                {
                    "id": f"understat-team-{provider_id}",
                    "provider_id": provider_id,
                    "name": team["title"],
                    "competition_id": league,
                    "season_id": f"{league}-{season}",
                    "matches": len(history),
                    "goals": sum(int(row.get("scored", 0)) for row in history),
                    "xg": sum(float(row.get("xG", 0)) for row in history),
                    "goals_against": sum(int(row.get("missed", 0)) for row in history),
                    "xga": sum(float(row.get("xGA", 0)) for row in history),
                    "xpts": sum(float(row.get("xpts", 0)) for row in history),
                    "points": sum(points),
                    "wins": sum(1 for value in points if value == 3),
                    "form": [
                        sum(points[max(0, index - 4) : index + 1])
                        for index in range(len(points))
                    ],
                    "ppda_att": sum(float(row.get("ppda", {}).get("att", 0)) for row in history),
                    "ppda_def": sum(float(row.get("ppda", {}).get("def", 0)) for row in history),
                }
            )
        return normalized

    @staticmethod
    def _normalize_managers(
        league: str, season: int, teams: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for team in teams:
            coach = team.get("coach") or {}
            name = str(coach.get("name") or "").strip()
            if not name:
                continue
            contract = coach.get("contract") or {}
            provider_id = str(coach.get("id") or Pipeline._team_key(name))
            rows.append(
                {
                    "id": f"football-data-manager-{provider_id}-{league}-{season}",
                    "provider_id": provider_id,
                    "name": name,
                    "team_name": Pipeline._canonical_team_name(str(team.get("name") or "")),
                    "competition_id": league,
                    "season_id": f"{league}-{season}",
                    "contract_start": contract.get("start"),
                    "contract_until": contract.get("until"),
                }
            )
        return rows

    @staticmethod
    def _canonical_team_name(value: str) -> str:
        aliases = {
            "north london fc": "Arsenal FC",
            "arsenal": "Arsenal FC",
            "fc internazionale milano": "Inter",
            "internazionale": "Inter",
            "inter milan": "Inter",
            "fc bayern münchen": "Bayern Munich",
            "fc bayern munchen": "Bayern Munich",
            "paris saint-germain fc": "Paris Saint Germain",
            "tottenham hotspur fc": "Tottenham",
        }
        return aliases.get(value.casefold().strip(), value.strip())

    @staticmethod
    def _team_key(value: str) -> str:
        canonical = Pipeline._canonical_team_name(value).casefold()
        ascii_name = unicodedata.normalize("NFKD", canonical).encode("ascii", "ignore").decode()
        return re.sub(r"\b(fc|cf|ac|ssc|calcio|club|de|futbol)\b|[^a-z0-9]", "", ascii_name)

    @staticmethod
    def _find_team(
        teams: list[dict[str, Any]], competition_id: str, season_id: str, name: str
    ) -> dict[str, Any] | None:
        candidates = [
            team
            for team in teams
            if team["competition_id"] == competition_id and team["season_id"] == season_id
        ]
        target = Pipeline._team_key(name)
        for team in candidates:
            if Pipeline._team_key(team["name"]) == target:
                return team
        scored = [
            (
                SequenceMatcher(None, target, Pipeline._team_key(team["name"])).ratio(),
                team,
            )
            for team in candidates
        ]
        best = max(scored, key=lambda item: item[0], default=None)
        if best and best[0] >= 0.75:
            return best[1]
        return None

    @staticmethod
    def _current_api_football_coach(
        team_id: int, coaches: list[dict[str, Any]]
    ) -> tuple[dict[str, Any], dict[str, Any]] | None:
        candidates: list[tuple[str, dict[str, Any], dict[str, Any]]] = []
        fallback: tuple[str, dict[str, Any], dict[str, Any]] | None = None
        for coach in coaches:
            for career in coach.get("career") or []:
                career_team = career.get("team") or {}
                if career_team.get("id") != team_id:
                    continue
                start = str(career.get("start") or "")
                record = (start, coach, career)
                if not career.get("end"):
                    candidates.append(record)
                if fallback is None or start > fallback[0]:
                    fallback = record
        selected = max(candidates, key=lambda item: item[0], default=fallback)
        if not selected:
            return None
        return selected[1], selected[2]

    @staticmethod
    def _manager_tenure_label(start: str | None, until: str | None) -> str:
        if start and until:
            return f"Contract {str(start)[:10]} to {str(until)[:10]}"
        if start:
            return f"Current since {str(start)[:10]}"
        return "Current coach"

    @staticmethod
    def _normalize_shots(match: dict[str, Any], payload: dict[str, Any]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for side, is_home in (("h", True), ("a", False)):
            team_id = match["home_team_id"] if is_home else match["away_team_id"]
            for shot in payload.get(side, []):
                rows.append(
                    {
                        "id": f"understat-shot-{shot['id']}",
                        "match_id": match["id"],
                        "player_id": f"understat-player-{shot['player_id']}",
                        "player": shot["player"],
                        "team_id": team_id,
                        "team": shot.get("h_team") if is_home else shot.get("a_team"),
                        "minute": int(shot["minute"]),
                        "x": float(shot["X"]),
                        "y": float(shot["Y"]),
                        "xg": float(shot["xG"]),
                        "result": shot["result"],
                        "situation": shot.get("situation"),
                        "body_part": shot.get("shotType"),
                        "is_home": is_home,
                    }
                )
        return rows

    @staticmethod
    def _write_parquet(path: Path, rows: list[dict[str, Any]]) -> None:
        if not rows:
            return
        pl.DataFrame(rows).write_parquet(path, compression="zstd")

    @staticmethod
    def _write_json(path: Path, value: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _content_hash(value: Any) -> str:
        encoded = json.dumps(value, sort_keys=True, default=str).encode()
        return hashlib.sha256(encoded).hexdigest()

    @staticmethod
    def _source_commit() -> str:
        if commit := os.getenv("GITHUB_SHA"):
            return commit
        try:
            return subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=Path(__file__).resolve().parents[2],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        except (OSError, subprocess.CalledProcessError):
            return "unknown"
