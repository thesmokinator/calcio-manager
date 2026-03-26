"""Match data models."""

from __future__ import annotations

from datetime import date
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from calcio_manager.models.enums import MatchEventType, MatchResult
from calcio_manager.models.team import Lineup


class MatchEvent(BaseModel):
    """A single event during a match."""

    minute: int = Field(ge=0)
    event_type: MatchEventType
    team_id: UUID | None = None
    player_id: UUID | None = None
    assist_player_id: UUID | None = None
    commentary: str = ""


class PenaltyShootout(BaseModel):
    """Result of a penalty shootout."""

    home_scores: list[bool] = Field(default_factory=list)
    away_scores: list[bool] = Field(default_factory=list)

    @property
    def home_goals(self) -> int:
        """Total penalties scored by home team."""
        return sum(self.home_scores)

    @property
    def away_goals(self) -> int:
        """Total penalties scored by away team."""
        return sum(self.away_scores)


class MatchScore(BaseModel):
    """Score of a match including penalties."""

    home_goals: int = 0
    away_goals: int = 0
    penalty_shootout: PenaltyShootout | None = None

    @property
    def is_draw_regular_time(self) -> bool:
        """Check if the match ended in a draw in regular time."""
        return self.home_goals == self.away_goals

    @property
    def home_penalty_goals(self) -> int:
        """Home team penalty goals (0 if no shootout)."""
        if self.penalty_shootout is None:
            return 0
        return self.penalty_shootout.home_goals

    @property
    def away_penalty_goals(self) -> int:
        """Away team penalty goals (0 if no shootout)."""
        if self.penalty_shootout is None:
            return 0
        return self.penalty_shootout.away_goals

    @property
    def display(self) -> str:
        """Human-readable score string."""
        base = f"{self.home_goals} - {self.away_goals}"
        if self.penalty_shootout:
            base += f" (rig. {self.home_penalty_goals}-{self.away_penalty_goals})"
        return base


class Match(BaseModel):
    """A single match between two teams."""

    id: UUID = Field(default_factory=uuid4)
    home_team_id: UUID
    away_team_id: UUID
    competition_id: UUID
    match_day: int = 1
    match_date: date | None = None
    played: bool = False
    score: MatchScore = MatchScore()
    result: MatchResult | None = None
    events: list[MatchEvent] = Field(default_factory=list)
    home_lineup: Lineup = Lineup()
    away_lineup: Lineup = Lineup()

    # Statistics
    home_possession: float = 50.0
    away_possession: float = 50.0
    home_shots: int = 0
    away_shots: int = 0
    home_shots_on_target: int = 0
    away_shots_on_target: int = 0
    home_fouls: int = 0
    away_fouls: int = 0
    home_corners: int = 0
    away_corners: int = 0

    def get_points(self, team_id: UUID) -> int:
        """Get CSI points earned by a team in this match (3-2-1-0 system)."""
        if self.result is None:
            return 0

        is_home = team_id == self.home_team_id

        if self.result == MatchResult.HOME_WIN:
            return 3 if is_home else 0
        elif self.result == MatchResult.AWAY_WIN:
            return 0 if is_home else 3
        elif self.result == MatchResult.HOME_WIN_PENALTIES:
            return 2 if is_home else 1
        elif self.result == MatchResult.AWAY_WIN_PENALTIES:
            return 1 if is_home else 2
        elif self.result == MatchResult.FORFEIT_HOME:
            return 0 if is_home else 3
        elif self.result == MatchResult.FORFEIT_AWAY:
            return 3 if is_home else 0
        return 0
