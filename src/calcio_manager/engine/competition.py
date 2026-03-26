"""Competition management: standings, results, tiebreakers."""

from __future__ import annotations

from uuid import UUID

from calcio_manager.models.competition import Competition, StandingRow
from calcio_manager.models.enums import MatchResult
from calcio_manager.models.match import Match


def initialize_standings(competition: Competition, team_names: dict[UUID, str]) -> None:
    """Initialize empty standings for all teams in a competition."""
    competition.standings = [
        StandingRow(team_id=tid, team_name=team_names.get(tid, ""))
        for tid in competition.team_ids
    ]


def update_standings(competition: Competition, match: Match) -> None:
    """Update standings after a match result."""
    if match.result is None:
        return

    home_row = next(
        (r for r in competition.standings if r.team_id == match.home_team_id), None
    )
    away_row = next(
        (r for r in competition.standings if r.team_id == match.away_team_id), None
    )

    if home_row is None or away_row is None:
        return

    home_row.played += 1
    away_row.played += 1
    home_row.goals_for += match.score.home_goals
    home_row.goals_against += match.score.away_goals
    away_row.goals_for += match.score.away_goals
    away_row.goals_against += match.score.home_goals

    # Update head-to-head tracking
    away_id_str = str(match.away_team_id)
    home_id_str = str(match.home_team_id)

    home_row.h2h_goals_for[away_id_str] = (
        home_row.h2h_goals_for.get(away_id_str, 0) + match.score.home_goals
    )
    home_row.h2h_goals_against[away_id_str] = (
        home_row.h2h_goals_against.get(away_id_str, 0) + match.score.away_goals
    )
    away_row.h2h_goals_for[home_id_str] = (
        away_row.h2h_goals_for.get(home_id_str, 0) + match.score.away_goals
    )
    away_row.h2h_goals_against[home_id_str] = (
        away_row.h2h_goals_against.get(home_id_str, 0) + match.score.home_goals
    )

    # Points and result counters
    home_points = match.get_points(match.home_team_id)
    away_points = match.get_points(match.away_team_id)

    home_row.points += home_points
    away_row.points += away_points

    home_row.h2h_points[away_id_str] = (
        home_row.h2h_points.get(away_id_str, 0) + home_points
    )
    away_row.h2h_points[home_id_str] = (
        away_row.h2h_points.get(home_id_str, 0) + away_points
    )

    if match.result == MatchResult.HOME_WIN:
        home_row.wins += 1
        away_row.losses += 1
    elif match.result == MatchResult.AWAY_WIN:
        away_row.wins += 1
        home_row.losses += 1
    elif match.result == MatchResult.HOME_WIN_PENALTIES:
        home_row.wins_penalties += 1
        away_row.losses_penalties += 1
    elif match.result == MatchResult.AWAY_WIN_PENALTIES:
        away_row.wins_penalties += 1
        home_row.losses_penalties += 1
    elif match.result == MatchResult.FORFEIT_HOME:
        away_row.wins += 1
        home_row.losses += 1
    elif match.result == MatchResult.FORFEIT_AWAY:
        home_row.wins += 1
        away_row.losses += 1

    # Update card counts from match events
    from calcio_manager.models.enums import MatchEventType

    for event in match.events:
        if event.event_type == MatchEventType.YELLOW_CARD:
            if event.team_id == match.home_team_id:
                home_row.yellow_cards += 1
            else:
                away_row.yellow_cards += 1
        elif event.event_type in (MatchEventType.RED_CARD, MatchEventType.SECOND_YELLOW):
            if event.team_id == match.home_team_id:
                home_row.red_cards += 1
            else:
                away_row.red_cards += 1


def sort_standings(standings: list[StandingRow]) -> list[StandingRow]:
    """Sort standings using CSI tiebreaker rules.

    Order:
    1. Points (descending)
    2. Head-to-head points between tied teams (descending)
    3. Head-to-head goal difference between tied teams (descending)
    4. Overall goal difference (descending)
    5. Goals scored (descending)
    6. Discipline score (ascending — fewer cards is better)
    """

    def _sort_key(row: StandingRow) -> tuple[int, int, int, int, int]:
        return (
            row.points,
            row.goal_difference,
            row.goals_for,
            -row.discipline_score,
            row.played,
        )

    # First pass: sort by basic criteria
    sorted_rows = sorted(standings, key=_sort_key, reverse=True)

    # Second pass: resolve ties using head-to-head
    i = 0
    while i < len(sorted_rows):
        # Find group of teams tied on points
        j = i + 1
        while j < len(sorted_rows) and sorted_rows[j].points == sorted_rows[i].points:
            j += 1

        if j - i > 1:
            # Multiple teams tied on points — apply h2h tiebreaker
            tied = sorted_rows[i:j]
            tied_ids = {str(r.team_id) for r in tied}

            def _h2h_key(
                row: StandingRow,
                tied_ids: set[str] = tied_ids,
            ) -> tuple[int, int, int, int, int]:
                h2h_pts = sum(
                    row.h2h_points.get(tid, 0)
                    for tid in tied_ids
                    if tid != str(row.team_id)
                )
                h2h_gf = sum(
                    row.h2h_goals_for.get(tid, 0)
                    for tid in tied_ids
                    if tid != str(row.team_id)
                )
                h2h_ga = sum(
                    row.h2h_goals_against.get(tid, 0)
                    for tid in tied_ids
                    if tid != str(row.team_id)
                )
                return (
                    h2h_pts,
                    h2h_gf - h2h_ga,
                    row.goal_difference,
                    row.goals_for,
                    -row.discipline_score,
                )

            tied.sort(key=_h2h_key, reverse=True)
            sorted_rows[i:j] = tied

        i = j

    return sorted_rows
