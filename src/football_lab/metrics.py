from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from statistics import median


def per_90(value: float, minutes: int) -> float | None:
    if minutes <= 0:
        return None
    return value * 90 / minutes


def percentile_rank(value: float, population: Sequence[float], higher_is_better: bool = True) -> int:
    if not population:
        raise ValueError("population must not be empty")
    below = sum(item < value for item in population)
    equal = sum(item == value for item in population)
    percentile = round(100 * (below + 0.5 * equal) / len(population))
    return percentile if higher_is_better else 100 - percentile


def expected_points(home_xg: float, away_xg: float) -> tuple[float, float]:
    """Estimate expected points using independent Poisson goal distributions."""
    from math import exp, factorial

    max_goals = 10
    home_probs = [exp(-home_xg) * home_xg**goals / factorial(goals) for goals in range(max_goals)]
    away_probs = [exp(-away_xg) * away_xg**goals / factorial(goals) for goals in range(max_goals)]
    home_win = draw = away_win = 0.0
    for home_goals, home_probability in enumerate(home_probs):
        for away_goals, away_probability in enumerate(away_probs):
            probability = home_probability * away_probability
            if home_goals > away_goals:
                home_win += probability
            elif home_goals == away_goals:
                draw += probability
            else:
                away_win += probability
    return 3 * home_win + draw, 3 * away_win + draw


def median_restart_delay(events: Iterable[Mapping[str, object]]) -> float | None:
    """Return observed restart delay without assigning intent."""
    delays = [
        float(event["restart_delay_seconds"])
        for event in events
        if event.get("restart_delay_seconds") is not None
        and event.get("event_type") in {"goal_kick", "throw_in", "corner", "free_kick"}
    ]
    return median(delays) if delays else None


def substitution_state_profile(events: Iterable[Mapping[str, object]]) -> dict[str, float]:
    counts = {"leading": 0, "drawing": 0, "trailing": 0}
    for event in events:
        if event.get("event_type") != "substitution":
            continue
        state = event.get("score_state")
        if state in counts:
            counts[str(state)] += 1
    total = sum(counts.values())
    if not total:
        return {key: 0.0 for key in counts}
    return {key: value * 100 / total for key, value in counts.items()}
