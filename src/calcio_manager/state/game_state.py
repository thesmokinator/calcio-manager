"""Central game state management."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from calcio_manager.models.competition import Competition
from calcio_manager.models.config import GameConfig
from calcio_manager.models.match import Match
from calcio_manager.models.season import Season
from calcio_manager.models.team import Team


class GameState(BaseModel):
    """Complete state of a game in progress."""

    config: GameConfig
    season: Season
    teams: dict[str, Team] = Field(
        default_factory=dict,
        description="Team UUID string -> Team mapping",
    )
    competitions: dict[str, Competition] = Field(
        default_factory=dict,
        description="Competition UUID string -> Competition mapping",
    )
    matches: dict[str, Match] = Field(
        default_factory=dict,
        description="Match UUID string -> Match mapping",
    )
    human_team_id: UUID | None = None

    @property
    def human_team(self) -> Team | None:
        """Return the human-controlled team."""
        if self.human_team_id is None:
            return None
        return self.teams.get(str(self.human_team_id))

    @property
    def human_competition(self) -> Competition | None:
        """Return the competition containing the human team."""
        if self.human_team_id is None:
            return None
        for comp in self.competitions.values():
            if self.human_team_id in comp.team_ids:
                return comp
        return None

    @property
    def current_competition(self) -> Competition | None:
        """Return the human team's competition, or the first available."""
        return self.human_competition or (
            next(iter(self.competitions.values())) if self.competitions else None
        )

    def get_team(self, team_id: UUID) -> Team | None:
        """Look up a team by UUID."""
        return self.teams.get(str(team_id))

    def get_match(self, match_id: UUID) -> Match | None:
        """Look up a match by UUID."""
        return self.matches.get(str(match_id))

    def get_next_match_for_team(self, team_id: UUID) -> Match | None:
        """Find the next unplayed match for a specific team."""
        for md in self.season.calendar:
            if md.played:
                continue
            for mid in md.match_ids:
                match = self.matches.get(str(mid))
                if match and not match.played and (
                    match.home_team_id == team_id
                    or match.away_team_id == team_id
                ):
                        return match
        return None

    def get_matches_for_day(self, day_number: int) -> list[Match]:
        """Get all matches for a given match day."""
        for md in self.season.calendar:
            if md.day_number == day_number:
                return [
                    self.matches[str(mid)]
                    for mid in md.match_ids
                    if str(mid) in self.matches
                ]
        return []
