"""Season management: transitions, year computation, and career continuity."""

from __future__ import annotations

from datetime import date

from calcio_manager.engine.calendar import (
    generate_match_schedule,
    generate_round_robin,
)
from calcio_manager.engine.competition import initialize_standings
from calcio_manager.models.enums import SeasonPhase
from calcio_manager.models.season import Season
from calcio_manager.state.game_state import GameState


def compute_season_year(start_year: int) -> str:
    """Compute a season year string from a start year.

    Args:
        start_year: The year the season starts (e.g., 2025).

    Returns:
        Season string like "2025-2026".
    """
    return f"{start_year}-{start_year + 1}"


def default_start_year() -> int:
    """Return the default start year (previous year relative to today)."""
    return date.today().year - 1


def advance_season(game_state: GameState) -> None:
    """Generate a new season when the current one ends.

    - Increments the season year
    - Keeps all teams (squads persist)
    - Generates new round-robin schedules for all competitions
    - Resets standings
    - Updates the Season object with new calendar

    Args:
        game_state: The current game state (modified in place).
    """
    # Parse current season year and increment
    current_start = int(game_state.season.year.split("-")[0])
    new_start = current_start + 1
    new_year = compute_season_year(new_start)

    # Reset competitions and regenerate schedules
    all_match_days = []
    all_matches = {}

    for _comp_id_str, competition in game_state.competitions.items():
        # Reset standings
        team_names = {
            team.id: team.name
            for tid_str, team in game_state.teams.items()
            if team.id in competition.team_ids
        }
        initialize_standings(competition, team_names)

        # Reset competition state
        competition.current_match_day = 0
        competition.completed = False

        # Generate new schedule
        rounds = generate_round_robin(competition.team_ids, home_and_away=True)
        matches, match_days = generate_match_schedule(
            rounds,
            competition.id,
            season_year=new_year,
        )

        competition.match_ids = [m.id for m in matches]
        competition.total_match_days = len(match_days)

        for m in matches:
            all_matches[str(m.id)] = m
        all_match_days.extend(match_days)

    # Sort all match days by date
    all_match_days.sort(key=lambda md: md.date)

    # Create new season
    game_state.season = Season(
        year=new_year,
        competition_ids=[comp.id for comp in game_state.competitions.values()],
        calendar=all_match_days,
        current_date=date(new_start, 8, 1),
        phase=SeasonPhase.PRE_SEASON,
    )

    game_state.matches = all_matches
    game_state.config.season_year = new_year
