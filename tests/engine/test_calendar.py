"""Tests for calendar and schedule generation."""

from uuid import uuid4

from calcio_manager.engine.calendar import generate_match_schedule, generate_round_robin


def test_round_robin_all_teams_play():
    """Every team should play against every other team."""
    team_ids = [uuid4() for _ in range(8)]
    rounds = generate_round_robin(team_ids, home_and_away=False)

    # Each team should play 7 matches (n-1 for round-robin)
    team_matches: dict[str, int] = {str(tid): 0 for tid in team_ids}

    for round_matches in rounds:
        for home, away in round_matches:
            team_matches[str(home)] += 1
            team_matches[str(away)] += 1

    for tid, count in team_matches.items():
        assert count == 7, f"Team {tid} played {count} matches, expected 7"


def test_round_robin_no_duplicate_fixtures():
    """No team should play the same opponent twice in single round-robin."""
    team_ids = [uuid4() for _ in range(8)]
    rounds = generate_round_robin(team_ids, home_and_away=False)

    seen = set()
    for round_matches in rounds:
        for home, away in round_matches:
            pair = frozenset([home, away])
            assert pair not in seen, f"Duplicate fixture: {home} vs {away}"
            seen.add(pair)


def test_home_and_away_doubles_matches():
    """Andata/ritorno should produce double the rounds."""
    team_ids = [uuid4() for _ in range(8)]

    single = generate_round_robin(team_ids, home_and_away=False)
    double = generate_round_robin(team_ids, home_and_away=True)

    assert len(double) == len(single) * 2


def test_home_and_away_reverse():
    """Return leg should swap home/away."""
    team_ids = [uuid4() for _ in range(8)]
    rounds = generate_round_robin(team_ids, home_and_away=True)

    n = len(rounds) // 2
    andata = rounds[:n]
    ritorno = rounds[n:]

    for a_round, r_round in zip(andata, ritorno, strict=True):
        for (a_home, a_away), (r_home, r_away) in zip(a_round, r_round, strict=True):
            assert a_home == r_away
            assert a_away == r_home


def test_no_team_plays_itself():
    """No team should ever be scheduled against itself."""
    team_ids = [uuid4() for _ in range(8)]
    rounds = generate_round_robin(team_ids, home_and_away=True)

    for round_matches in rounds:
        for home, away in round_matches:
            assert home != away


def test_no_team_plays_twice_same_day():
    """No team should play more than once on the same match day."""
    team_ids = [uuid4() for _ in range(8)]
    rounds = generate_round_robin(team_ids, home_and_away=True)

    for round_matches in rounds:
        teams_playing = []
        for home, away in round_matches:
            teams_playing.extend([home, away])
        assert len(teams_playing) == len(set(teams_playing)), (
            "A team is playing twice on the same match day"
        )


def test_generate_match_schedule():
    """Match schedule should create Match and MatchDay objects."""
    team_ids = [uuid4() for _ in range(8)]
    comp_id = uuid4()
    rounds = generate_round_robin(team_ids, home_and_away=True)

    matches, match_days = generate_match_schedule(rounds, comp_id)

    assert len(match_days) == len(rounds)
    assert len(matches) == sum(len(r) for r in rounds)

    # All matches should reference the competition
    for m in matches:
        assert m.competition_id == comp_id
        assert not m.played


def test_odd_number_of_teams():
    """Round-robin should work with odd number of teams (byes)."""
    team_ids = [uuid4() for _ in range(7)]
    rounds = generate_round_robin(team_ids, home_and_away=False)

    # With 7 teams (+ 1 bye), there should be 7 rounds
    assert len(rounds) == 7

    # Each round should have 3 matches (one team has bye)
    for round_matches in rounds:
        assert len(round_matches) == 3
