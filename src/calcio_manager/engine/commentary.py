"""Locale-aware commentary engine for match events."""

from __future__ import annotations

import random
import tomllib
from pathlib import Path
from uuid import UUID

from calcio_manager.i18n import current_locale
from calcio_manager.models.enums import MatchEventType
from calcio_manager.models.match import MatchEvent
from calcio_manager.models.player import Player
from calcio_manager.models.team import Team

DATA_DIR = Path(__file__).parent.parent / "data"

# Map event types to TOML section names
_EVENT_SECTION_MAP: dict[MatchEventType, str] = {
    MatchEventType.GOAL: "goal",
    MatchEventType.CHANCE: "chance",
    MatchEventType.SHOT_SAVED: "shot_saved",
    MatchEventType.SHOT_WIDE: "shot_wide",
    MatchEventType.SHOT_POST: "shot_post",
    MatchEventType.FOUL: "foul",
    MatchEventType.YELLOW_CARD: "yellow_card",
    MatchEventType.RED_CARD: "red_card",
    MatchEventType.SECOND_YELLOW: "second_yellow",
    MatchEventType.CORNER: "corner",
    MatchEventType.KICK_OFF: "kick_off",
    MatchEventType.HALF_TIME: "half_time",
    MatchEventType.FULL_TIME: "full_time",
    MatchEventType.PENALTY_SHOOTOUT_START: "penalty_shootout_start",
    MatchEventType.PENALTY_SCORED: "penalty_scored",
    MatchEventType.PENALTY_MISSED: "penalty_missed",
    MatchEventType.PENALTY_SAVED: "penalty_saved",
    MatchEventType.POSSESSION: "possession",
    MatchEventType.TIMEOUT: "timeout",
    MatchEventType.SUBSTITUTION: "substitution",
}


class CommentaryEngine:
    """Generates text commentary for match events in the current locale."""

    def __init__(self) -> None:
        self._templates: dict[str, list[str]] = {}
        self._load_templates()

    def _load_templates(self) -> None:
        """Load commentary templates from the locale-specific TOML file."""
        lang = current_locale()
        path = DATA_DIR / f"commentary_{lang}.toml"
        if not path.exists():
            path = DATA_DIR / "commentary_it.toml"
        with open(path, "rb") as f:
            data = tomllib.load(f)

        for section_name, section_data in data.items():
            if isinstance(section_data, dict) and "templates" in section_data:
                self._templates[section_name] = section_data["templates"]
                # Also load special template variants
                for key, value in section_data.items():
                    if key != "templates" and isinstance(value, list):
                        self._templates[f"{section_name}_{key}"] = value

    def generate(
        self,
        event: MatchEvent,
        home_team: Team,
        away_team: Team,
        home_goals: int = 0,
        away_goals: int = 0,
        players: dict[UUID, Player] | None = None,
    ) -> str:
        """Generate commentary text for a match event.

        Args:
            event: The match event to commentate.
            home_team: Home team.
            away_team: Away team.
            home_goals: Current home goals.
            away_goals: Current away goals.
            players: Optional player lookup dict.
        """
        section = _EVENT_SECTION_MAP.get(event.event_type)
        if section is None:
            return ""

        # Build template variables
        team = home_team if event.team_id == home_team.id else away_team
        opponent = away_team if event.team_id == home_team.id else home_team

        player_name = ""
        if event.player_id and players:
            player = players.get(event.player_id)
            if player:
                player_name = player.short_name

        assist_name = ""
        if event.assist_player_id and players:
            assist_player = players.get(event.assist_player_id)
            if assist_player:
                assist_name = assist_player.short_name

        score = f"{home_goals} - {away_goals}"

        vars_dict = {
            "team": team.name,
            "opponent": opponent.name,
            "player": player_name,
            "scorer": player_name,
            "assist": assist_name,
            "home": home_team.name,
            "away": away_team.name,
            "home_goals": str(home_goals),
            "away_goals": str(away_goals),
            "score": score,
        }

        # Choose template variant
        template_key = section
        if event.event_type == MatchEventType.GOAL and assist_name:
            # Prefer assist variant if available
            assist_key = f"{section}_templates_with_assist"
            if assist_key in self._templates:
                template_key = assist_key

        templates = self._templates.get(template_key, [])
        if not templates:
            templates = self._templates.get(section, [])

        if not templates:
            return f"{event.minute}' - {event.event_type.value}"

        template = random.choice(templates)

        try:
            return template.format(**vars_dict)
        except KeyError:
            return template
