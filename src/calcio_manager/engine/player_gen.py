"""Player and team generation for CSI amateur football."""

from __future__ import annotations

import random
import tomllib
from pathlib import Path

from calcio_manager.models.enums import AgeCategory, PlayerRole, TacticStyle
from calcio_manager.models.player import (
    GoalkeepingAttributes,
    MentalAttributes,
    PhysicalAttributes,
    Player,
    PlayerAttributes,
    SeasonStats,
    TechnicalAttributes,
)
from calcio_manager.models.team import Formation, Team

DATA_DIR = Path(__file__).parent.parent / "data"


def _load_names() -> dict[str, list[str]]:
    """Load Italian name pools from TOML file."""
    names_file = DATA_DIR / "names_it.toml"
    with open(names_file, "rb") as f:
        data = tomllib.load(f)
    return {
        "first_names": data["names"]["first_names"],
        "last_names": data["names"]["last_names"],
    }


def _load_team_data(province: str = "varese") -> dict[str, list[str]]:
    """Load team generation data from TOML file."""
    names_file = DATA_DIR / "names_it.toml"
    with open(names_file, "rb") as f:
        data = tomllib.load(f)
    return {
        "prefixes": data["teams"]["prefixes"],
        "base_names": data["teams"]["base_names"],
        "locations": data["teams"].get(province, {}).get("locations", []),
    }


def _random_attr(base: int, variance: int = 4) -> int:
    """Generate a random attribute value around a base, clamped 1-20."""
    return max(1, min(20, base + random.randint(-variance, variance)))


def _age_adjusted_base(age: int, peak_base: int) -> int:
    """Adjust attribute base by age (peak at 26-30 for amateurs)."""
    if age < 20:
        return max(1, peak_base - 3)
    elif age < 26:
        return peak_base - 1
    elif age <= 30:
        return peak_base  # Peak years
    elif age <= 35:
        return max(1, peak_base - 1)
    elif age <= 40:
        return max(1, peak_base - 2)
    else:
        return max(1, peak_base - 4)


def _physical_age_penalty(age: int) -> int:
    """Physical attributes decline faster with age in amateur football."""
    if age <= 30:
        return 0
    elif age <= 35:
        return -2
    elif age <= 40:
        return -4
    else:
        return -6


def _mental_age_bonus(age: int) -> int:
    """Mental attributes improve with experience."""
    if age < 22:
        return -2
    elif age < 26:
        return 0
    elif age <= 35:
        return 2
    else:
        return 3


def generate_player(
    role: PlayerRole,
    category: AgeCategory = AgeCategory.OPEN,
    quality_base: int = 10,
    season: str = "2025-2026",
    names: dict[str, list[str]] | None = None,
) -> Player:
    """Generate a random player with attributes appropriate for CSI amateur level.

    Args:
        role: Player position.
        category: Age category (affects age range).
        quality_base: Base quality level (1-20, 10 = average amateur).
        season: Current season string.
        names: Pre-loaded name pools (optional).
    """
    if names is None:
        names = _load_names()

    first_name = random.choice(names["first_names"])
    last_name = random.choice(names["last_names"])

    # Age based on category
    age_ranges = {
        AgeCategory.OPEN: (18, 45),
        AgeCategory.MASTER_30: (30, 50),
        AgeCategory.MASTER_40: (40, 55),
        AgeCategory.JUNIORES: (16, 18),
        AgeCategory.ALLIEVI: (14, 16),
        AgeCategory.UNDER_14: (12, 14),
        AgeCategory.UNDER_12: (10, 12),
    }
    min_age, max_age = age_ranges.get(category, (18, 45))
    age = random.randint(min_age, max_age)

    # Adjust base by age
    adj_base = _age_adjusted_base(age, quality_base)
    phys_penalty = _physical_age_penalty(age)
    mental_bonus = _mental_age_bonus(age)

    # Generate attributes
    technical = TechnicalAttributes(
        passing=_random_attr(adj_base),
        dribbling=_random_attr(adj_base),
        finishing=_random_attr(adj_base + (2 if role == PlayerRole.FWD else -1)),
        first_touch=_random_attr(adj_base),
    )

    mental = MentalAttributes(
        positioning=_random_attr(adj_base + mental_bonus + (2 if role == PlayerRole.DEF else 0)),
        decisions=_random_attr(adj_base + mental_bonus),
        leadership=_random_attr(adj_base + mental_bonus - 2),
        teamwork=_random_attr(adj_base + mental_bonus),
    )

    physical = PhysicalAttributes(
        pace=_random_attr(max(1, adj_base + phys_penalty + (2 if role == PlayerRole.FWD else 0))),
        stamina=_random_attr(max(1, adj_base + phys_penalty)),
        strength=_random_attr(
            max(1, adj_base + phys_penalty + (1 if role == PlayerRole.DEF else 0))
        ),
    )

    # Goalkeeping: high for GK, low for others
    if role == PlayerRole.GK:
        goalkeeping = GoalkeepingAttributes(
            reflexes=_random_attr(adj_base + 3),
            handling=_random_attr(adj_base + 2),
        )
    else:
        goalkeeping = GoalkeepingAttributes(
            reflexes=_random_attr(3, variance=2),
            handling=_random_attr(3, variance=2),
        )

    attributes = PlayerAttributes(
        technical=technical,
        mental=mental,
        physical=physical,
        goalkeeping=goalkeeping,
    )

    player = Player(
        first_name=first_name,
        last_name=last_name,
        age=age,
        role=role,
        overall=1,  # Placeholder, calculated below
        attributes=attributes,
        current_season_stats=SeasonStats(season=season),
    )
    player.overall = player.calculate_overall()

    return player


def generate_squad(
    category: AgeCategory = AgeCategory.OPEN,
    quality_base: int = 10,
    squad_size: int = 14,
    season: str = "2025-2026",
) -> list[Player]:
    """Generate a complete squad for a C7 team.

    Standard squad: 2 GK, 4 DEF, 4 MID, 4 FWD (14 players).
    """
    names = _load_names()

    # Role distribution for C7
    role_counts = {
        PlayerRole.GK: 2,
        PlayerRole.DEF: max(3, (squad_size - 2) // 3),
        PlayerRole.MID: max(3, (squad_size - 2) // 3),
        PlayerRole.FWD: 0,  # Remainder
    }
    role_counts[PlayerRole.FWD] = squad_size - sum(role_counts.values())

    squad: list[Player] = []
    used_names: set[str] = set()

    for role, count in role_counts.items():
        for _ in range(count):
            # Ensure unique names
            attempts = 0
            while attempts < 50:
                player = generate_player(
                    role=role,
                    category=category,
                    quality_base=quality_base,
                    season=season,
                    names=names,
                )
                if player.full_name not in used_names:
                    used_names.add(player.full_name)
                    squad.append(player)
                    break
                attempts += 1
            else:
                squad.append(player)

    return squad


def generate_team(
    name: str,
    city: str,
    province: str = "Varese",
    quality_base: int = 10,
    category: AgeCategory = AgeCategory.OPEN,
    season: str = "2025-2026",
    is_human: bool = False,
    colors: tuple[str, str] | None = None,
) -> Team:
    """Generate a complete team with squad."""
    squad = generate_squad(
        category=category,
        quality_base=quality_base,
        season=season,
    )

    # Random colors (if none provided)
    colors_pool = [
        ("bianco", "nero"), ("rosso", "blu"), ("giallo", "verde"),
        ("bianco", "rosso"), ("azzurro", "bianco"), ("nero", "verde"),
        ("arancione", "nero"), ("viola", "bianco"), ("blu", "giallo"),
        ("rosso", "nero"), ("verde", "bianco"), ("grigio", "rosso"),
    ]

    formation = random.choice(Formation.default_formations())
    tactic = random.choice(list(TacticStyle))

    return Team(
        name=name,
        city=city,
        province=province,
        colors=colors if colors else random.choice(colors_pool),
        reputation=max(10, min(90, quality_base * 5 + random.randint(-10, 10))),
        squad=squad,
        formation=formation,
        tactic=tactic,
        is_human=is_human,
    )


def generate_league_teams(
    num_teams: int = 8,
    province: str = "varese",
    category: AgeCategory = AgeCategory.OPEN,
    season: str = "2025-2026",
) -> list[Team]:
    """Generate a set of teams for a league with varied quality.

    Teams have varying quality bases to create competitive imbalance
    (some stronger teams, some weaker — like real amateur leagues).
    """
    team_data = _load_team_data(province)
    locations = team_data["locations"]
    prefixes = team_data["prefixes"]
    base_names = team_data["base_names"]

    if len(locations) < num_teams:
        locations = locations * ((num_teams // len(locations)) + 1)

    random.shuffle(locations)
    random.shuffle(base_names)

    # Assign unique colour pairs so every team in the league is distinguishable.
    colors_pool = [
        ("bianco", "nero"), ("rosso", "blu"), ("giallo", "verde"),
        ("bianco", "rosso"), ("azzurro", "bianco"), ("nero", "verde"),
        ("arancione", "nero"), ("viola", "bianco"), ("blu", "giallo"),
        ("rosso", "nero"), ("verde", "bianco"), ("grigio", "rosso"),
    ]
    random.shuffle(colors_pool)

    teams: list[Team] = []
    used_names: set[str] = set()

    for i in range(num_teams):
        city = locations[i]
        prefix = random.choice(prefixes)
        base_name = base_names[i % len(base_names)]

        # Some teams use city name, some use base name, some combine
        name_style = random.choice(["city", "base", "combined"])
        if name_style == "city":
            team_name = f"{prefix} {city}"
        elif name_style == "base":
            team_name = f"{prefix} {base_name}"
        else:
            team_name = f"{base_name} {city}"

        if team_name in used_names:
            team_name = f"{prefix} {base_name} {city}"
        used_names.add(team_name)

        # Quality varies: 1-2 strong teams, 2-3 average, rest weaker
        if i < 2:
            quality = random.randint(12, 14)  # Strong
        elif i < 5:
            quality = random.randint(9, 11)  # Average
        else:
            quality = random.randint(7, 9)  # Weaker

        teams.append(generate_team(
            name=team_name,
            city=city,
            province=province.capitalize(),
            quality_base=quality,
            category=category,
            season=season,
            colors=colors_pool[i % len(colors_pool)],
        ))

    return teams
