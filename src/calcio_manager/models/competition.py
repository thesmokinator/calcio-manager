"""Competition and standings data models."""

from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from calcio_manager.models.config import CompetitionRules
from calcio_manager.models.enums import (
    AgeCategory,
    CompetitionPhase,
    CompetitionType,
    Division,
    GameFormat,
)


class StandingRow(BaseModel):
    """A single row in the league standings."""

    team_id: UUID
    team_name: str = ""
    played: int = 0
    wins: int = 0
    wins_penalties: int = 0
    losses_penalties: int = 0
    losses: int = 0
    goals_for: int = 0
    goals_against: int = 0
    points: int = 0

    # Head-to-head tracking for tiebreakers
    h2h_points: dict[str, int] = Field(
        default_factory=dict,
        description="Points in head-to-head matches: opponent_id -> points",
    )
    h2h_goals_for: dict[str, int] = Field(default_factory=dict)
    h2h_goals_against: dict[str, int] = Field(default_factory=dict)

    # Discipline
    yellow_cards: int = 0
    red_cards: int = 0

    @property
    def goal_difference(self) -> int:
        """Goal difference."""
        return self.goals_for - self.goals_against

    @property
    def matches_total(self) -> int:
        """Total matches (should equal played)."""
        return self.wins + self.wins_penalties + self.losses_penalties + self.losses

    @property
    def discipline_score(self) -> int:
        """Discipline score for tiebreaker (lower is better)."""
        return self.yellow_cards + self.red_cards * 3


class Competition(BaseModel):
    """A CSI competition (league, cup, or tournament)."""

    id: UUID = Field(default_factory=uuid4)
    name: str
    format: GameFormat = GameFormat.C7
    category: AgeCategory = AgeCategory.OPEN
    competition_type: CompetitionType = CompetitionType.LEAGUE
    phase: CompetitionPhase = CompetitionPhase.TERRITORIAL
    division: Division = Division.SERIE_ORO
    province: str = "Varese"
    region: str = "Lombardia"
    team_ids: list[UUID] = Field(default_factory=list)
    standings: list[StandingRow] = Field(default_factory=list)
    match_ids: list[UUID] = Field(default_factory=list)
    rules: CompetitionRules = CompetitionRules()
    current_match_day: int = 0
    total_match_days: int = 0
    completed: bool = False

    @property
    def num_teams(self) -> int:
        """Number of teams in the competition."""
        return len(self.team_ids)

    def get_sorted_standings(self) -> list[StandingRow]:
        """Return standings sorted by CSI tiebreaker rules.

        CSI tiebreaker order:
        1. Points
        2. Head-to-head points
        3. Head-to-head goal difference
        4. Overall goal difference
        5. Goals scored
        6. Discipline (fewer cards = better)
        """

        def sort_key(row: StandingRow) -> tuple[int, int, int, int, int, int]:
            return (
                row.points,
                0,  # H2H points computed separately for tied teams
                0,  # H2H goal diff computed separately
                row.goal_difference,
                row.goals_for,
                -row.discipline_score,  # Negative because lower is better
            )

        return sorted(self.standings, key=sort_key, reverse=True)
