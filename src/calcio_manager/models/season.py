"""Season data model."""

from datetime import date
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from calcio_manager.models.enums import SeasonPhase


class MatchDay(BaseModel):
    """A single match day in the calendar."""

    day_number: int
    date: date
    match_ids: list[UUID] = Field(default_factory=list)
    played: bool = False


class Season(BaseModel):
    """A game season tracking competitions and calendar."""

    id: UUID = Field(default_factory=uuid4)
    year: str  # e.g. "2025-2026"
    competition_ids: list[UUID] = Field(default_factory=list)
    calendar: list[MatchDay] = Field(default_factory=list)
    current_date: date = date(2025, 9, 1)
    phase: SeasonPhase = SeasonPhase.PRE_SEASON

    @property
    def next_match_day(self) -> MatchDay | None:
        """Return the next unplayed match day."""
        for md in self.calendar:
            if not md.played:
                return md
        return None

    @property
    def current_match_day_number(self) -> int:
        """Return the current match day number."""
        for md in self.calendar:
            if not md.played:
                return md.day_number
        return len(self.calendar)

    @property
    def is_season_over(self) -> bool:
        """Check if all match days have been played."""
        return all(md.played for md in self.calendar)
