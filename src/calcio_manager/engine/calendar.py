"""Calendar and schedule generation for CSI competitions."""

from __future__ import annotations

from datetime import date, timedelta
from uuid import UUID

from calcio_manager.models.match import Match
from calcio_manager.models.season import MatchDay


def generate_round_robin(
    team_ids: list[UUID],
    home_and_away: bool = True,
) -> list[list[tuple[UUID, UUID]]]:
    """Generate a round-robin schedule using the Berger algorithm.

    Args:
        team_ids: List of team UUIDs.
        home_and_away: If True, generate both legs (andata e ritorno).

    Returns:
        List of rounds, each containing a list of (home_id, away_id) tuples.
    """
    teams = list(team_ids)
    n = len(teams)

    # If odd number of teams, add a bye
    bye_id = None
    if n % 2 != 0:
        bye_id = UUID("00000000-0000-0000-0000-000000000000")
        teams.append(bye_id)
        n += 1

    rounds: list[list[tuple[UUID, UUID]]] = []
    half = n // 2

    # Berger table: fix first team, rotate the rest
    rotation = teams[1:]

    for _ in range(n - 1):
        round_matches: list[tuple[UUID, UUID]] = []

        # First team vs last in rotation
        round_matches.append((teams[0], rotation[-1]))

        # Pair remaining teams
        for j in range(1, half):
            home = rotation[j - 1]
            away = rotation[n - 2 - j]
            round_matches.append((home, away))

        # Remove bye matches
        round_matches = [
            (h, a) for h, a in round_matches if h != bye_id and a != bye_id
        ]

        rounds.append(round_matches)

        # Rotate: move last element to front
        rotation = [rotation[-1]] + rotation[:-1]

    if home_and_away:
        # Ritorno: swap home/away for all matches
        return_rounds = [
            [(away, home) for home, away in round_matches]
            for round_matches in rounds
        ]
        rounds.extend(return_rounds)

    return rounds


def season_start_date(season_year: str) -> date:
    """Compute the third Saturday of September for a season year.

    Args:
        season_year: Season string like "2025-2026".

    Returns:
        Date of the third Saturday of September.
    """
    start_year = int(season_year.split("-")[0])
    # Find first day of September
    sept_1 = date(start_year, 9, 1)
    # Find first Saturday (weekday 5)
    days_until_saturday = (5 - sept_1.weekday()) % 7
    first_saturday = sept_1 + timedelta(days=days_until_saturday)
    # Third Saturday = first + 14 days
    return first_saturday + timedelta(days=14)


def generate_match_schedule(
    rounds: list[list[tuple[UUID, UUID]]],
    competition_id: UUID,
    start_date: date | None = None,
    interval_days: int = 7,
    season_year: str = "2025-2026",
) -> tuple[list[Match], list[MatchDay]]:
    """Convert round-robin rounds into Match and MatchDay objects.

    Args:
        rounds: Output of generate_round_robin.
        competition_id: UUID of the competition.
        start_date: Date of the first match day. If None, computed from season_year.
        interval_days: Days between match days (typically 7 for weekly).
        season_year: Season string, used to compute start_date if not provided.

    Returns:
        Tuple of (all matches, all match days).
    """
    if start_date is None:
        start_date = season_start_date(season_year)
    all_matches: list[Match] = []
    match_days: list[MatchDay] = []

    for round_num, round_matches in enumerate(rounds):
        match_day_date = start_date + timedelta(days=round_num * interval_days)
        day_match_ids: list[UUID] = []

        for home_id, away_id in round_matches:
            match = Match(
                home_team_id=home_id,
                away_team_id=away_id,
                competition_id=competition_id,
                match_day=round_num + 1,
                match_date=match_day_date,
            )
            all_matches.append(match)
            day_match_ids.append(match.id)

        match_days.append(MatchDay(
            day_number=round_num + 1,
            date=match_day_date,
            match_ids=day_match_ids,
        ))

    return all_matches, match_days
