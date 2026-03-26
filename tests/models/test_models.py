"""Tests for data models."""

from calcio_manager.models.config import CompetitionRules, GameConfig
from calcio_manager.models.enums import AgeCategory, GameFormat, MatchResult
from calcio_manager.models.match import Match, MatchScore, PenaltyShootout
from calcio_manager.models.team import Formation


def test_game_config_defaults():
    """Default config should be C7 Open in Varese."""
    config = GameConfig()

    assert config.format == GameFormat.C7
    assert config.category == AgeCategory.OPEN
    assert config.province == "Varese"
    assert config.rules.half_duration_minutes == 25
    assert config.rules.players_on_pitch == 7
    assert config.rules.penalties_after_draw is True


def test_competition_rules_by_category():
    """Rules should adapt to different age categories."""
    open_rules = CompetitionRules.for_category(AgeCategory.OPEN)
    assert open_rules.half_duration_minutes == 25

    master40 = CompetitionRules.for_category(AgeCategory.MASTER_40)
    assert master40.half_duration_minutes == 20

    under12 = CompetitionRules.for_category(AgeCategory.UNDER_12)
    assert under12.half_duration_minutes == 8
    assert under12.num_periods == 4


def test_competition_rules_c5():
    """C5 rules should differ from C7."""
    c5 = CompetitionRules.for_category(AgeCategory.OPEN, GameFormat.C5)
    assert c5.players_on_pitch == 5
    assert c5.min_players_to_play == 3
    assert c5.rolling_subs is True
    assert c5.timeout_per_half == 0
    assert c5.numerical_inferiority_minutes == 2


def test_formation_validation():
    """Formation should validate that outfield players sum to 6."""
    f = Formation(name="2-3-1", defenders=2, midfielders=3, forwards=1)
    assert f.defenders + f.midfielders + f.forwards == 6

    import pytest

    with pytest.raises(ValueError):
        Formation(name="bad", defenders=2, midfielders=2, forwards=1)


def test_default_formations():
    """All default formations should be valid."""
    formations = Formation.default_formations()
    assert len(formations) >= 4

    for f in formations:
        assert f.defenders + f.midfielders + f.forwards == 6


def test_match_score_display():
    """Match score should display correctly."""
    score = MatchScore(home_goals=2, away_goals=1)
    assert score.display == "2 - 1"
    assert score.is_draw_regular_time is False

    draw = MatchScore(
        home_goals=1,
        away_goals=1,
        penalty_shootout=PenaltyShootout(
            home_scores=[True, True, True, False, True],
            away_scores=[True, False, True, True, False],
        ),
    )
    assert draw.is_draw_regular_time is True
    assert "rig." in draw.display


def test_match_get_points_csi():
    """Match.get_points should return correct CSI points."""
    from uuid import uuid4

    home_id = uuid4()
    away_id = uuid4()
    comp_id = uuid4()

    # Regular win
    match = Match(
        home_team_id=home_id,
        away_team_id=away_id,
        competition_id=comp_id,
        result=MatchResult.HOME_WIN,
    )
    assert match.get_points(home_id) == 3
    assert match.get_points(away_id) == 0

    # Penalty win for home
    match.result = MatchResult.HOME_WIN_PENALTIES
    assert match.get_points(home_id) == 2
    assert match.get_points(away_id) == 1

    # Penalty win for away
    match.result = MatchResult.AWAY_WIN_PENALTIES
    assert match.get_points(home_id) == 1
    assert match.get_points(away_id) == 2

    # Regular away win
    match.result = MatchResult.AWAY_WIN
    assert match.get_points(home_id) == 0
    assert match.get_points(away_id) == 3

    # Forfeit
    match.result = MatchResult.FORFEIT_HOME
    assert match.get_points(home_id) == 0
    assert match.get_points(away_id) == 3
