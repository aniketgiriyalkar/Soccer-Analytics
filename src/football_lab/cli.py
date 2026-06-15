from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime

from football_lab.config import Settings, UNDERSTAT_LEAGUES
from football_lab.pipeline import Pipeline


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="football-lab")
    commands = root.add_subparsers(dest="command", required=True)

    backfill = commands.add_parser("backfill", help="Ingest a historical league-season range")
    backfill.add_argument("--league", choices=UNDERSTAT_LEAGUES, required=True)
    backfill.add_argument("--from-season", type=int, required=True)
    backfill.add_argument("--to-season", type=int, required=True)
    backfill.add_argument("--include-shots", action="store_true")

    refresh = commands.add_parser("refresh-season", help="Refresh one domestic league season")
    refresh.add_argument("--league", choices=UNDERSTAT_LEAGUES, required=True)
    refresh.add_argument("--season", type=int, required=True)
    refresh.add_argument("--include-shots", action="store_true")

    commands.add_parser("refresh-current", help="Refresh every domestic league's active season")
    commands.add_parser("rebuild-aggregates", help="Recreate DuckDB views over Parquet")
    commands.add_parser("audit-coverage", help="Report incomplete or unverified coverage")
    commands.add_parser("export-schema", help="Publish JSON schemas for normalized entities")
    commands.add_parser("publish-frontend", help="Publish compact frontend JSON from Parquet")
    return root


def main() -> None:
    args = parser().parse_args()
    pipeline = Pipeline(Settings())
    current_start_year = datetime.now(UTC).year if datetime.now(UTC).month >= 7 else datetime.now(UTC).year - 1

    if args.command == "backfill":
        pipeline.backfill(args.league, args.from_season, args.to_season, args.include_shots)
    elif args.command == "refresh-season":
        pipeline.ingest_understat_season(args.league, args.season, args.include_shots)
    elif args.command == "refresh-current":
        for league in UNDERSTAT_LEAGUES:
            # The league page contains current player, team, match, and xG aggregates.
            # Shot-level refreshes remain an explicit/manual operation to keep daily
            # source traffic bounded.
            pipeline.ingest_understat_season(league, current_start_year, include_shots=False)
            pipeline.ingest_current_managers(league, current_start_year)
    elif args.command == "rebuild-aggregates":
        pipeline.rebuild_aggregates()
    elif args.command == "audit-coverage":
        print(json.dumps(pipeline.audit_coverage(), indent=2))
    elif args.command == "export-schema":
        pipeline.export_schema()
    elif args.command == "publish-frontend":
        pipeline.publish_frontend()


if __name__ == "__main__":
    main()
