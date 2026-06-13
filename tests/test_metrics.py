from football_lab.metrics import (
    expected_points,
    median_restart_delay,
    per_90,
    percentile_rank,
    substitution_state_profile,
)


def test_per_90_handles_minutes_and_zero() -> None:
    assert per_90(10, 900) == 1
    assert per_90(10, 0) is None


def test_percentile_can_reward_lower_discipline_values() -> None:
    population = [0.1, 0.2, 0.3, 0.4]
    assert percentile_rank(0.1, population, higher_is_better=False) > 80


def test_expected_points_are_bounded() -> None:
    home, away = expected_points(2.0, 0.7)
    assert 0 <= home <= 3
    assert 0 <= away <= 3
    assert home > away


def test_game_management_is_based_on_observed_restart_events() -> None:
    events = [
        {"event_type": "goal_kick", "restart_delay_seconds": 14},
        {"event_type": "throw_in", "restart_delay_seconds": 10},
        {"event_type": "shot", "restart_delay_seconds": 99},
    ]
    assert median_restart_delay(events) == 12


def test_substitution_profile_uses_match_state() -> None:
    events = [
        {"event_type": "substitution", "score_state": "leading"},
        {"event_type": "substitution", "score_state": "leading"},
        {"event_type": "substitution", "score_state": "drawing"},
    ]
    result = substitution_state_profile(events)
    assert round(result["leading"]) == 67
    assert round(result["drawing"]) == 33
