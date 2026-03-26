"""Tests for competition management and standings."""

from calcio_manager.engine.competition import (
    initialize_standings,
    sort_standings,
    update_standings,
)
from calcio_manager.engine.match import MatchEngine
from calcio_manager.engine.player_gen import generate_league_teams
from calcio_manager.models.competition import Competition
from calcio_manager.models.config import CompetitionRules
from calcio_manager.models.enums import AgeCategory, GameFormat, MatchResult


def _setup_competition(num_teams: int = 8):
    """Create a competition with generated teams."""
    teams = generate_league_teams(num_teams, "varese")
    rules = CompetitionRules.for_category(AgeCategory.OPEN, GameFormat.C7)

    comp = Competition(
        name="Test League",
        team_ids=[t.id for t in teams],
        rules=rules,
    )
    team_names = {t.id: t.name for t in teams}
    initialize_standings(comp, team_names)
    return comp, teams, rules


def test_initialize_standings():
    """Standings should be initialized for all teams with zero values."""
    comp, teams, _ = _setup_competition()

    assert len(comp.standings) == len(teams)
    for row in comp.standings:
        assert row.points == 0
        assert row.played == 0
        assert row.wins == 0
        assert row.goals_for == 0


def test_standings_update_after_win():
    """Standings should correctly reflect a win (3 points)."""
    comp, teams, rules = _setup_competition()
    engine = MatchEngine()

    # Simulate a match
    match = engine.simulate(teams[0], teams[1], rules)
    update_standings(comp, match)

    # Find the winner's standing
    if match.result in (MatchResult.HOME_WIN, MatchResult.HOME_WIN_PENALTIES):
        winner_id = teams[0].id
    else:
        winner_id = teams[1].id

    winner_row = next(r for r in comp.standings if r.team_id == winner_id)
    assert winner_row.played == 1
    assert winner_row.points > 0


def test_csi_points_in_standings():
    """Verify CSI 3-2-1-0 points system in standings after multiple matches."""
    comp, teams, rules = _setup_competition(4)
    engine = MatchEngine()

    total_points = 0

    # Play a few matches
    for i in range(0, len(teams) - 1, 2):
        match = engine.simulate(teams[i], teams[i + 1], rules)
        update_standings(comp, match)

        # Each match distributes either 3+0 or 2+1 points
        home_pts = match.get_points(teams[i].id)
        away_pts = match.get_points(teams[i + 1].id)
        total_points += home_pts + away_pts
        assert home_pts + away_pts == 3  # Always 3 total per match in CSI

    # Total points should equal 3 * number_of_matches
    standing_total = sum(r.points for r in comp.standings)
    assert standing_total == total_points


def test_sort_standings_by_points():
    """Teams with more points should rank higher."""
    comp, teams, rules = _setup_competition(4)
    engine = MatchEngine()

    # Simulate several matches
    for _ in range(3):
        for i in range(len(teams)):
            for j in range(i + 1, len(teams)):
                match = engine.simulate(teams[i], teams[j], rules)
                update_standings(comp, match)

    sorted_rows = sort_standings(comp.standings)

    # Points should be in descending order
    for i in range(len(sorted_rows) - 1):
        assert sorted_rows[i].points >= sorted_rows[i + 1].points


def test_all_matches_distribute_3_points():
    """In CSI, every match distributes exactly 3 points total."""
    comp, teams, rules = _setup_competition(4)
    engine = MatchEngine()

    for _ in range(50):
        match = engine.simulate(teams[0], teams[1], rules)
        home_pts = match.get_points(teams[0].id)
        away_pts = match.get_points(teams[1].id)
        assert home_pts + away_pts == 3, (
            f"Expected 3 total points, got {home_pts + away_pts} "
            f"(result: {match.result})"
        )


def test_head_to_head_tracking():
    """Head-to-head stats should be tracked in standings."""
    comp, teams, rules = _setup_competition(4)
    engine = MatchEngine()

    match = engine.simulate(teams[0], teams[1], rules)
    update_standings(comp, match)

    row_0 = next(r for r in comp.standings if r.team_id == teams[0].id)
    row_1 = next(r for r in comp.standings if r.team_id == teams[1].id)

    # H2H data should exist
    assert str(teams[1].id) in row_0.h2h_points
    assert str(teams[0].id) in row_1.h2h_points
