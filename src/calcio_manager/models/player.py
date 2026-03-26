"""Player data models."""

from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from calcio_manager.models.enums import MoraleLevel, PlayerRole


class TechnicalAttributes(BaseModel):
    """Technical skills of a player (1-20 scale)."""

    passing: int = Field(ge=1, le=20, description="Passaggio")
    dribbling: int = Field(ge=1, le=20, description="Dribbling")
    finishing: int = Field(ge=1, le=20, description="Tiro")
    first_touch: int = Field(ge=1, le=20, description="Controllo palla")


class MentalAttributes(BaseModel):
    """Mental attributes of a player (1-20 scale)."""

    positioning: int = Field(ge=1, le=20, description="Posizionamento")
    decisions: int = Field(ge=1, le=20, description="Decisioni")
    leadership: int = Field(ge=1, le=20, description="Leadership")
    teamwork: int = Field(ge=1, le=20, description="Gioco di squadra")


class PhysicalAttributes(BaseModel):
    """Physical attributes of a player (1-20 scale)."""

    pace: int = Field(ge=1, le=20, description="Velocità")
    stamina: int = Field(ge=1, le=20, description="Resistenza")
    strength: int = Field(ge=1, le=20, description="Forza")


class GoalkeepingAttributes(BaseModel):
    """Goalkeeping-specific attributes (1-20 scale)."""

    reflexes: int = Field(ge=1, le=20, description="Riflessi")
    handling: int = Field(ge=1, le=20, description="Presa")


class PlayerAttributes(BaseModel):
    """Complete set of player attributes."""

    technical: TechnicalAttributes
    mental: MentalAttributes
    physical: PhysicalAttributes
    goalkeeping: GoalkeepingAttributes = GoalkeepingAttributes(reflexes=5, handling=5)


class Injury(BaseModel):
    """Player injury information."""

    description: str
    days_remaining: int = Field(ge=0)


class SeasonStats(BaseModel):
    """Player statistics for a single season."""

    season: str  # e.g. "2025-2026"
    appearances: int = 0
    goals: int = 0
    assists: int = 0
    yellow_cards: int = 0
    red_cards: int = 0
    minutes_played: int = 0
    average_rating: float = 0.0


class Player(BaseModel):
    """A football player in the game."""

    id: UUID = Field(default_factory=uuid4)
    first_name: str
    last_name: str
    age: int = Field(ge=14, le=60)
    role: PlayerRole
    overall: int = Field(ge=1, le=20, description="Overall rating derived from attributes")
    attributes: PlayerAttributes
    condition: float = Field(ge=0.0, le=1.0, default=1.0, description="Physical condition 0-1")
    morale: MoraleLevel = MoraleLevel.NORMAL
    injury: Injury | None = None
    suspended: bool = False
    yellow_card_accumulation: int = 0
    current_season_stats: SeasonStats = SeasonStats(season="2025-2026")
    history: list[SeasonStats] = Field(default_factory=list)

    @property
    def full_name(self) -> str:
        """Return the player's full name."""
        return f"{self.first_name} {self.last_name}"

    @property
    def short_name(self) -> str:
        """Return abbreviated name (e.g., 'M. Rossi')."""
        return f"{self.first_name[0]}. {self.last_name}"

    @property
    def is_available(self) -> bool:
        """Check if the player is available for selection."""
        return self.injury is None and not self.suspended

    def calculate_overall(self) -> int:
        """Calculate overall rating based on role and attributes."""
        attrs = self.attributes
        tech = attrs.technical
        ment = attrs.mental
        phys = attrs.physical

        if self.role == PlayerRole.GK:
            gk = attrs.goalkeeping
            score = (
                gk.reflexes * 3 + gk.handling * 3
                + ment.positioning * 2 + phys.pace * 1 + phys.strength * 1
            ) / 10
        elif self.role == PlayerRole.DEF:
            score = (
                ment.positioning * 3 + phys.strength * 2 + phys.pace * 1
                + tech.passing * 2 + ment.teamwork * 1 + ment.decisions * 1
            ) / 10
        elif self.role == PlayerRole.MID:
            score = (
                tech.passing * 3 + ment.decisions * 2 + ment.teamwork * 2
                + phys.stamina * 1 + tech.dribbling * 1 + ment.positioning * 1
            ) / 10
        else:  # FWD
            score = (
                tech.finishing * 3 + tech.dribbling * 2 + phys.pace * 2
                + tech.first_touch * 1 + ment.positioning * 1 + ment.decisions * 1
            ) / 10

        return max(1, min(20, round(score)))
