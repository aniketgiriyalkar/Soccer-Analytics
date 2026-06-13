from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CoverageLevel(StrEnum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    UNAVAILABLE = "unavailable"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Competition(StrictModel):
    id: str
    name: str
    country: str | None = None
    kind: str = Field(pattern="^(league|cup)$")


class Season(StrictModel):
    id: str
    competition_id: str
    start_year: int = Field(ge=1900, le=2200)
    label: str


class Team(StrictModel):
    id: str
    provider_id: str
    name: str
    competition_id: str
    season_id: str


class Player(StrictModel):
    id: str
    provider_id: str
    name: str
    team_id: str
    season_id: str
    position: str | None = None
    minutes: int = Field(default=0, ge=0)


class Match(StrictModel):
    id: str
    provider_id: str
    competition_id: str
    season_id: str
    home_team_id: str
    away_team_id: str
    kickoff: datetime
    home_goals: int | None = Field(default=None, ge=0)
    away_goals: int | None = Field(default=None, ge=0)
    home_xg: float | None = Field(default=None, ge=0)
    away_xg: float | None = Field(default=None, ge=0)
    stage: str | None = None


class Shot(StrictModel):
    id: str
    match_id: str
    player_id: str | None = None
    team_id: str
    minute: int = Field(ge=0, le=150)
    x: float = Field(ge=0, le=1)
    y: float = Field(ge=0, le=1)
    xg: float = Field(ge=0, le=1)
    result: str
    situation: str | None = None
    body_part: str | None = None
    is_home: bool


class MatchEvent(StrictModel):
    id: str
    match_id: str
    team_id: str | None = None
    player_id: str | None = None
    minute: int = Field(ge=0, le=150)
    second: int | None = Field(default=None, ge=0, le=59)
    event_type: str
    detail: str | None = None
    score_state: str | None = Field(default=None, pattern="^(leading|drawing|trailing)$")


class ManagerTenure(StrictModel):
    id: str
    manager_id: str
    manager_name: str
    team_id: str
    start_date: date
    end_date: date | None = None
    matches: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def end_must_follow_start(self) -> "ManagerTenure":
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date must not precede start_date")
        return self


class MetricCoverage(StrictModel):
    competition_id: str
    season_id: str
    standard_stats: CoverageLevel
    xg: CoverageLevel
    events: CoverageLevel
    expected_matches: int | None = Field(default=None, ge=0)
    ingested_matches: int = Field(default=0, ge=0)
    generated_at: datetime

    @property
    def match_ratio(self) -> float | None:
        if not self.expected_matches:
            return None
        return self.ingested_matches / self.expected_matches
