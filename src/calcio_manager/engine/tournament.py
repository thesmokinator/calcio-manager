"""Tournament structure: gironi calculation, team distribution, and playoff config."""

from __future__ import annotations

import random

from calcio_manager.models.team import Team


def calculate_gironi_structure(
    num_teams_available: int,
    min_per_group: int = 6,
    max_per_group: int = 10,
) -> tuple[int, int]:
    """Calculate the number of groups and teams per group.

    Distributes teams into groups of 6-10, preferring ~8 per group.

    Args:
        num_teams_available: Total teams to distribute (including human team).
        min_per_group: Minimum teams per group.
        max_per_group: Maximum teams per group.

    Returns:
        Tuple of (num_groups, teams_per_group).
    """
    if num_teams_available <= max_per_group:
        return 1, max(min_per_group, num_teams_available)

    # Try to find the best split around 8 teams per group
    best_groups = 1
    best_size = num_teams_available
    best_diff = abs(8 - num_teams_available)

    for groups in range(2, num_teams_available // min_per_group + 1):
        size = num_teams_available // groups
        if min_per_group <= size <= max_per_group:
            diff = abs(8 - size)
            if diff < best_diff:
                best_diff = diff
                best_groups = groups
                best_size = size

    return best_groups, best_size


def generate_gironi(
    all_teams: list[Team],
    num_groups: int,
) -> list[list[Team]]:
    """Distribute teams across groups using serpentine seeding by quality.

    Teams are sorted by squad average overall, then distributed in a
    serpentine pattern so each group has a mix of strong and weak teams.

    Args:
        all_teams: All teams to distribute.
        num_groups: Number of groups to create.

    Returns:
        List of groups, each containing a list of teams.
    """
    if num_groups <= 1:
        return [list(all_teams)]

    # Sort by quality (best first)
    sorted_teams = sorted(
        all_teams,
        key=lambda t: t.squad_average_overall,
        reverse=True,
    )

    gironi: list[list[Team]] = [[] for _ in range(num_groups)]

    for i, team in enumerate(sorted_teams):
        row = i // num_groups
        group_idx = i % num_groups if row % 2 == 0 else num_groups - 1 - (i % num_groups)
        gironi[group_idx].append(team)

    return gironi


def get_playoff_config(num_groups: int) -> dict[str, int | str]:
    """Return playoff structure based on number of gironi.

    Args:
        num_groups: Number of groups in the tournament.

    Returns:
        Dict with playoff configuration:
        - teams_per_group: How many teams qualify from each group
        - total_qualified: Total teams in playoffs
        - format: "semifinal", "quarterfinal", etc.
    """
    if num_groups == 1:
        return {
            "teams_per_group": 4,
            "total_qualified": 4,
            "format": "semifinal",
        }
    elif num_groups == 2:
        return {
            "teams_per_group": 2,
            "total_qualified": 4,
            "format": "semifinal",
        }
    elif num_groups <= 4:
        return {
            "teams_per_group": 2,
            "total_qualified": num_groups * 2,
            "format": "quarterfinal",
        }
    else:
        return {
            "teams_per_group": 1,
            "total_qualified": num_groups,
            "format": "round_of_16" if num_groups > 8 else "quarterfinal",
        }


def select_tournament_comuni(
    all_comuni: list[str],
    human_comune: str,
    num_groups: int,
    teams_per_group: int,
) -> list[str]:
    """Select random comuni for the tournament, excluding the human's comune.

    Args:
        all_comuni: All available comuni in the province.
        human_comune: The human player's comune (will be excluded from random pick).
        num_groups: Number of groups.
        teams_per_group: Teams per group.

    Returns:
        List of selected comuni (excluding human comune).
    """
    total_needed = num_groups * teams_per_group - 1  # -1 for human team
    available = [c for c in all_comuni if c != human_comune]
    random.shuffle(available)

    if len(available) < total_needed:
        return available

    return available[:total_needed]
