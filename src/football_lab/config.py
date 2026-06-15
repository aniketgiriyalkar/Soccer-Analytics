from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PARQUET_DIR = DATA_DIR / "parquet"
CHECKPOINT_DIR = DATA_DIR / "checkpoints"
PUBLIC_DATA_DIR = ROOT / "public" / "data"

UNDERSTAT_LEAGUES = {
    "premier-league": "EPL",
    "la-liga": "La_liga",
    "bundesliga": "Bundesliga",
    "serie-a": "Serie_A",
    "ligue-1": "Ligue_1",
}

FOOTBALL_DATA_COMPETITIONS = {
    "premier-league": "PL",
    "la-liga": "PD",
    "bundesliga": "BL1",
    "serie-a": "SA",
    "ligue-1": "FL1",
}

API_FOOTBALL_LEAGUES = {
    "premier-league": 39,
    "la-liga": 140,
    "bundesliga": 78,
    "serie-a": 135,
    "ligue-1": 61,
}

DISPLAY_NAMES = {
    "premier-league": "Premier League",
    "la-liga": "La Liga",
    "bundesliga": "Bundesliga",
    "serie-a": "Serie A",
    "ligue-1": "Ligue 1",
    "champions-league": "Champions League",
}


@dataclass(frozen=True)
class Settings:
    request_delay: float = 1.5
    earliest_season: int = 2014
    schema_version: str = "1.0"
