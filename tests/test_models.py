from datetime import date, datetime, timezone

import pytest
from pydantic import ValidationError

from football_lab.models import CoverageLevel, ManagerTenure, MetricCoverage, Shot


def test_manager_tenure_rejects_inverted_dates() -> None:
    with pytest.raises(ValidationError):
        ManagerTenure(
            id="tenure-1",
            manager_id="manager-1",
            manager_name="Manager",
            team_id="team-1",
            start_date=date(2025, 1, 1),
            end_date=date(2024, 1, 1),
        )


def test_shot_coordinates_are_normalized() -> None:
    with pytest.raises(ValidationError):
        Shot(
            id="shot-1",
            match_id="match-1",
            team_id="team-1",
            minute=42,
            x=1.2,
            y=0.5,
            xg=0.2,
            result="Saved",
            is_home=True,
        )


def test_coverage_ratio_is_explicit() -> None:
    coverage = MetricCoverage(
        competition_id="champions-league",
        season_id="2025",
        standard_stats=CoverageLevel.COMPLETE,
        xg=CoverageLevel.PARTIAL,
        events=CoverageLevel.PARTIAL,
        expected_matches=189,
        ingested_matches=100,
        generated_at=datetime.now(timezone.utc),
    )
    assert coverage.match_ratio == 100 / 189
