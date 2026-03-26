"""Tests for player and team generation."""

from calcio_manager.engine.player_gen import (
    generate_league_teams,
    generate_player,
    generate_squad,
    generate_team,
)
from calcio_manager.models.enums import AgeCategory, PlayerRole


def test_generate_player():
    """Generated player should have valid attributes."""
    player = generate_player(PlayerRole.FWD)

    assert player.first_name
    assert player.last_name
    assert 14 <= player.age <= 60
    assert player.role == PlayerRole.FWD
    assert 1 <= player.overall <= 20
    assert 1 <= player.attributes.technical.finishing <= 20
    assert 0.0 <= player.condition <= 1.0


def test_generate_goalkeeper():
    """Goalkeeper should have higher goalkeeping attributes."""
    gk = generate_player(PlayerRole.GK, quality_base=12)

    assert gk.role == PlayerRole.GK
    # GK should have reasonable reflexes
    assert gk.attributes.goalkeeping.reflexes >= 5


def test_generate_player_age_categories():
    """Players should be generated within the correct age range for their category."""
    for _ in range(20):
        open_player = generate_player(PlayerRole.MID, category=AgeCategory.OPEN)
        assert 18 <= open_player.age <= 45

        master30 = generate_player(PlayerRole.DEF, category=AgeCategory.MASTER_30)
        assert 30 <= master30.age <= 50

        master40 = generate_player(PlayerRole.FWD, category=AgeCategory.MASTER_40)
        assert 40 <= master40.age <= 55

        junior = generate_player(PlayerRole.MID, category=AgeCategory.JUNIORES)
        assert 16 <= junior.age <= 18


def test_generate_squad():
    """Squad should have correct number of players and role distribution."""
    squad = generate_squad(squad_size=14)

    assert len(squad) == 14

    gks = [p for p in squad if p.role == PlayerRole.GK]
    assert len(gks) == 2  # Always 2 GKs

    # Should have players in all outfield roles
    defs = [p for p in squad if p.role == PlayerRole.DEF]
    mids = [p for p in squad if p.role == PlayerRole.MID]
    fwds = [p for p in squad if p.role == PlayerRole.FWD]
    assert len(defs) >= 3
    assert len(mids) >= 3
    assert len(fwds) >= 2


def test_generate_team():
    """Generated team should have a complete squad and valid attributes."""
    team = generate_team("Pol. Test", "Varese")

    assert team.name == "Pol. Test"
    assert team.city == "Varese"
    assert len(team.squad) == 14
    assert team.formation is not None
    assert team.tactic is not None
    assert 10 <= team.reputation <= 90


def test_generate_league_teams():
    """League generation should create teams with varied quality."""
    teams = generate_league_teams(8, "varese")

    assert len(teams) == 8

    # All teams should have unique names
    names = {t.name for t in teams}
    assert len(names) == 8

    # Teams should have varied quality
    overalls = [t.squad_average_overall for t in teams]
    assert max(overalls) - min(overalls) > 1.0, (
        "Teams should have varied quality"
    )


def test_player_overall_calculation():
    """Overall rating should vary by role."""
    fwd = generate_player(PlayerRole.FWD, quality_base=12)
    gk = generate_player(PlayerRole.GK, quality_base=12)

    assert 1 <= fwd.overall <= 20
    assert 1 <= gk.overall <= 20
    # Both should have calculated overalls
    assert fwd.overall == fwd.calculate_overall()


def test_player_availability():
    """Available players should not be injured or suspended."""
    player = generate_player(PlayerRole.MID)
    assert player.is_available is True

    player.suspended = True
    assert player.is_available is False
