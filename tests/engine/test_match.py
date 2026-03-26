"""Tests for the match engine."""

from calcio_manager.engine.match import MatchEngine, simulate_penalty_shootout
from calcio_manager.engine.player_gen import generate_team
from calcio_manager.models.config import CompetitionRules
from calcio_manager.models.enums import (
    AgeCategory,
    GameFormat,
    MatchEventType,
    MatchResult,
)


def _make_teams(
    quality_home: int = 10, quality_away: int = 10
) -> tuple:
    """Create two test teams."""
    home = generate_team("Pol. Aurora", "Varese", quality_base=quality_home)
    away = generate_team("FC Stella", "Busto Arsizio", quality_base=quality_away)
    return home, away


def test_match_produces_result():
    """A match simulation always produces a valid result."""
    home, away = _make_teams()
    engine = MatchEngine()
    rules = CompetitionRules.for_category(AgeCategory.OPEN, GameFormat.C7)

    match = engine.simulate(home, away, rules)

    assert match.played is True
    assert match.result is not None
    assert match.result in (
        MatchResult.HOME_WIN,
        MatchResult.AWAY_WIN,
        MatchResult.HOME_WIN_PENALTIES,
        MatchResult.AWAY_WIN_PENALTIES,
    )


def test_no_draws_with_csi_rules():
    """CSI rules: every draw goes to penalties, so no draws in final result."""
    home, away = _make_teams()
    engine = MatchEngine()
    rules = CompetitionRules.for_category(AgeCategory.OPEN, GameFormat.C7)

    # Simulate 100 matches
    for _ in range(100):
        match = engine.simulate(home, away, rules)
        # Result should never be None (always a winner)
        assert match.result is not None
        # If regular time was a draw, penalties should have been played
        if match.score.is_draw_regular_time:
            assert match.score.penalty_shootout is not None
            assert match.result in (
                MatchResult.HOME_WIN_PENALTIES,
                MatchResult.AWAY_WIN_PENALTIES,
            )


def test_csi_points_system():
    """Verify the 3-2-1-0 CSI points system."""
    home, away = _make_teams()
    engine = MatchEngine()
    rules = CompetitionRules.for_category(AgeCategory.OPEN, GameFormat.C7)

    for _ in range(200):
        match = engine.simulate(home, away, rules)

        home_pts = match.get_points(home.id)
        away_pts = match.get_points(away.id)

        if match.result == MatchResult.HOME_WIN:
            assert home_pts == 3
            assert away_pts == 0
        elif match.result == MatchResult.AWAY_WIN:
            assert home_pts == 0
            assert away_pts == 3
        elif match.result == MatchResult.HOME_WIN_PENALTIES:
            assert home_pts == 2
            assert away_pts == 1
        elif match.result == MatchResult.AWAY_WIN_PENALTIES:
            assert home_pts == 1
            assert away_pts == 2


def test_stronger_team_wins_more():
    """A significantly stronger team should win more than 50% of matches."""
    strong = generate_team("FC Forte", "Milano", quality_base=15)
    weak = generate_team("US Debole", "Como", quality_base=6)
    engine = MatchEngine()
    rules = CompetitionRules.for_category(AgeCategory.OPEN, GameFormat.C7)

    strong_wins = 0
    total = 200

    for _ in range(total):
        match = engine.simulate(strong, weak, rules)
        if match.result in (MatchResult.HOME_WIN, MatchResult.HOME_WIN_PENALTIES):
            strong_wins += 1

    # Strong team should win at least 55% (conservative threshold)
    assert strong_wins / total >= 0.55, (
        f"Strong team only won {strong_wins}/{total} = {strong_wins/total:.1%}"
    )


def test_match_generates_events():
    """Match simulation should generate events."""
    home, away = _make_teams()
    engine = MatchEngine()
    rules = CompetitionRules.for_category(AgeCategory.OPEN, GameFormat.C7)

    match = engine.simulate(home, away, rules)

    assert len(match.events) > 0
    event_types = {e.event_type for e in match.events}
    # Should have at least some common event types
    assert len(event_types) >= 2


def test_match_statistics():
    """Match should track basic statistics."""
    home, away = _make_teams()
    engine = MatchEngine()
    rules = CompetitionRules.for_category(AgeCategory.OPEN, GameFormat.C7)

    match = engine.simulate(home, away, rules)

    # Possession should add up to ~100
    assert 90 <= match.home_possession + match.away_possession <= 110
    # Shots should be non-negative
    assert match.home_shots >= 0
    assert match.away_shots >= 0
    assert match.home_shots_on_target <= match.home_shots
    assert match.away_shots_on_target <= match.away_shots


def test_penalty_shootout():
    """Penalty shootout should always produce a winner."""
    home, away = _make_teams()

    for _ in range(50):
        shootout = simulate_penalty_shootout(home, away)
        # One team must win
        assert shootout.home_goals != shootout.away_goals
        # At least 5 rounds should have been played (unless decided early)
        min_rounds = min(len(shootout.home_scores), len(shootout.away_scores))
        assert min_rounds >= 3  # At least 3 rounds (could be decided early)


def test_forfeit_when_not_enough_players():
    """Team with too few players should forfeit 0-3."""
    home = generate_team("Pol. Aurora", "Varese", quality_base=10)
    away = generate_team("FC Stella", "Busto", quality_base=10)

    # Remove most players from home team
    home.squad = home.squad[:2]  # Only 2 players, below minimum 4

    engine = MatchEngine()
    rules = CompetitionRules.for_category(AgeCategory.OPEN, GameFormat.C7)
    match = engine.simulate(home, away, rules)

    assert match.result == MatchResult.FORFEIT_HOME
    assert match.score.home_goals == 0
    assert match.score.away_goals == 3


def test_event_listener():
    """Match engine should emit events to registered listeners."""
    home, away = _make_teams()
    engine = MatchEngine()
    rules = CompetitionRules.for_category(AgeCategory.OPEN, GameFormat.C7)

    events_received: list[MatchEventType] = []

    def listener(event):
        events_received.append(event.event_type)

    engine.add_listener(listener)
    engine.simulate(home, away, rules)

    assert len(events_received) > 0
    assert MatchEventType.KICK_OFF in events_received
    assert MatchEventType.HALF_TIME in events_received
    assert MatchEventType.FULL_TIME in events_received
