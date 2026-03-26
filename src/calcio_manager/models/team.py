"""Team data models."""

from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from calcio_manager.models.enums import PlayerRole, TacticStyle
from calcio_manager.models.player import Player


class Formation(BaseModel):
    """A team formation for C7 (excludes goalkeeper)."""

    name: str  # e.g., "2-3-1"
    defenders: int = Field(ge=0, le=6)
    midfielders: int = Field(ge=0, le=6)
    forwards: int = Field(ge=0, le=6)

    def model_post_init(self, __context: object) -> None:
        """Validate that formation adds up to 6 outfield players."""
        total = self.defenders + self.midfielders + self.forwards
        if total != 6:
            raise ValueError(
                f"Formation {self.name} has {total} outfield players, expected 6"
            )

    @classmethod
    def default_formations(cls) -> list["Formation"]:
        """Return the standard C7 formations."""
        return [
            cls(name="2-3-1", defenders=2, midfielders=3, forwards=1),
            cls(name="2-2-2", defenders=2, midfielders=2, forwards=2),
            cls(name="3-2-1", defenders=3, midfielders=2, forwards=1),
            cls(name="3-1-2", defenders=3, midfielders=1, forwards=2),
            cls(name="1-3-2", defenders=1, midfielders=3, forwards=2),
            cls(name="2-1-3", defenders=2, midfielders=1, forwards=3),
        ]


class Lineup(BaseModel):
    """Starting lineup and substitutes for a match."""

    starters: dict[str, UUID] = Field(
        default_factory=dict,
        description="Position slot -> Player ID mapping",
    )
    substitutes: list[UUID] = Field(default_factory=list)
    formation: Formation = Formation(name="2-3-1", defenders=2, midfielders=3, forwards=1)

    @property
    def starter_count(self) -> int:
        """Number of starting players."""
        return len(self.starters)


class TeamFinances(BaseModel):
    """Financial state of a team."""

    budget: int = Field(default=2000, description="Available budget in euros")
    registration_fees_paid: int = 0
    sponsor_income: int = 0
    tournament_prizes: int = 0
    expenses: int = 0

    @property
    def balance(self) -> int:
        """Current balance."""
        return (
            self.budget
            + self.sponsor_income
            + self.tournament_prizes
            - self.registration_fees_paid
            - self.expenses
        )


class Team(BaseModel):
    """A football team in the game."""

    id: UUID = Field(default_factory=uuid4)
    name: str
    city: str
    province: str = "Varese"
    colors: tuple[str, str] = ("bianco", "nero")
    reputation: int = Field(ge=1, le=100, default=50)
    squad: list[Player] = Field(default_factory=list)
    formation: Formation = Formation(name="2-3-1", defenders=2, midfielders=3, forwards=1)
    tactic: TacticStyle = TacticStyle.BALANCED
    finances: TeamFinances = TeamFinances()
    is_human: bool = False

    @property
    def available_players(self) -> list[Player]:
        """Return players available for selection (not injured/suspended)."""
        return [p for p in self.squad if p.is_available]

    @property
    def goalkeepers(self) -> list[Player]:
        """Return all goalkeepers in the squad."""
        return [p for p in self.squad if p.role == PlayerRole.GK]

    @property
    def outfield_players(self) -> list[Player]:
        """Return all non-goalkeeper players."""
        return [p for p in self.squad if p.role != PlayerRole.GK]

    @property
    def can_play(self) -> bool:
        """Check if the team has enough available players (CSI minimum: 4)."""
        return len(self.available_players) >= 4

    @property
    def squad_average_overall(self) -> float:
        """Average overall rating of the squad."""
        if not self.squad:
            return 0.0
        return sum(p.overall for p in self.squad) / len(self.squad)
