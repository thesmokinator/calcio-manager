"""Main Textual application for Calcio Manager."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from uuid import UUID

from textual.app import App

from calcio_manager.engine.calendar import generate_match_schedule, generate_round_robin
from calcio_manager.engine.competition import initialize_standings, update_standings
from calcio_manager.engine.match import MatchEngine
from calcio_manager.engine.season_manager import advance_season
from calcio_manager.i18n import t
from calcio_manager.models.competition import Competition
from calcio_manager.models.config import CompetitionRules, GameConfig
from calcio_manager.models.enums import (
    AgeCategory,
    CompetitionType,
    Division,
    GameFormat,
    SeasonPhase,
)
from calcio_manager.models.match import Match
from calcio_manager.models.season import Season
from calcio_manager.models.team import Team
from calcio_manager.state.game_state import GameState
from calcio_manager.state.save_load import load_game, save_game
from calcio_manager.ui.screens.calendar_screen import CalendarScreen
from calcio_manager.ui.screens.credits import CreditsScreen
from calcio_manager.ui.screens.game_hub import GameHubScreen
from calcio_manager.ui.screens.league_table import LeagueTableScreen
from calcio_manager.ui.screens.live_match import LiveMatchScreen
from calcio_manager.ui.screens.load_game import LoadGameScreen
from calcio_manager.ui.screens.main_menu import MainMenuScreen
from calcio_manager.ui.screens.new_game import NewGameResult, NewGameScreen
from calcio_manager.ui.screens.save_game import SaveGameScreen
from calcio_manager.ui.screens.settings import SettingsScreen
from calcio_manager.ui.screens.squad import SquadScreen

CSS_PATH = Path(__file__) / "ui" / "styles" / "app.tcss"


class CalcioManagerApp(App[None]):
    """Calcio Manager — 7-a-side Football Manager CSI."""

    ENABLE_COMMAND_PALETTE = False
    TITLE = "Calcio Manager"
    SUB_TITLE = t("app.subtitle")

    CSS = """
    Screen {
        background: $surface;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self.game_state: GameState | None = None

    def on_mount(self) -> None:
        """Show the main menu on startup."""
        self._show_main_menu()

    def _show_main_menu(self) -> None:
        """Display the main menu."""

        def on_menu_result(result: str | None) -> None:
            if result == "new-game":
                self._show_new_game()
            elif result == "load-game":
                self._show_load_game()
            elif result == "settings":
                self._show_settings()
            elif result == "credits":
                self._show_credits()

        self.push_screen(MainMenuScreen(), callback=on_menu_result)

    def _show_settings(self) -> None:
        """Show the settings screen."""

        def on_settings_done(_: None) -> None:
            self._show_main_menu()

        self.push_screen(SettingsScreen(), callback=on_settings_done)

    def _show_credits(self) -> None:
        """Show the credits screen."""

        def on_credits_done(_: None) -> None:
            self._show_main_menu()

        self.push_screen(CreditsScreen(), callback=on_credits_done)

    def _show_new_game(self) -> None:
        """Show the new game wizard."""

        def on_wizard_done(result: NewGameResult | None) -> None:
            if result is None:
                self._show_main_menu()
                return

            self._initialize_game_from_wizard(result)
            self._show_game_hub()

        self.push_screen(NewGameScreen(), callback=on_wizard_done)

    def _initialize_game_from_wizard(self, result: NewGameResult) -> None:
        """Set up a new game from the wizard result (multi-girone support)."""
        config = GameConfig(
            comune=result.comune,
            province=result.province,
            region=result.region,
            num_groups=len(result.gironi),
            teams_per_group=len(result.gironi[0]) if result.gironi else 8,
            season_year=result.season_year,
        )

        rules = CompetitionRules.for_category(AgeCategory.OPEN, GameFormat.C7)

        all_teams_dict: dict[str, Team] = {}
        all_competitions: dict[str, Competition] = {}
        all_matches_dict: dict[str, Match] = {}
        all_match_days = []

        for idx, girone_teams in enumerate(result.gironi):
            letter = chr(ord("A") + idx) if idx < 26 else str(idx + 1)

            # Create competition for this girone
            competition = Competition(
                girone=letter,
                format=GameFormat.C7,
                category=AgeCategory.OPEN,
                competition_type=CompetitionType.LEAGUE,
                division=Division.SERIE_ORO,
                province=result.province,
                region=result.region,
                team_ids=[team.id for team in girone_teams],
                rules=rules,
            )

            # Initialize standings
            team_names = {team.id: team.name for team in girone_teams}
            initialize_standings(competition, team_names)

            # Generate schedule
            rounds = generate_round_robin(
                [team.id for team in girone_teams], home_and_away=True,
            )
            matches, match_days = generate_match_schedule(
                rounds,
                competition.id,
                season_year=result.season_year,
            )

            competition.total_match_days = len(match_days)
            competition.match_ids = [m.id for m in matches]

            # Collect everything
            for team in girone_teams:
                all_teams_dict[str(team.id)] = team
            all_competitions[str(competition.id)] = competition
            for m in matches:
                all_matches_dict[str(m.id)] = m
            all_match_days.extend(match_days)

        # Sort match days by date for the unified calendar
        all_match_days.sort(key=lambda md: md.date)

        # Parse season start year for the season current_date
        start_year = int(result.season_year.split("-")[0])

        # Create season
        season = Season(
            year=result.season_year,
            competition_ids=[comp.id for comp in all_competitions.values()],
            calendar=all_match_days,
            current_date=date(start_year, 8, 1),
            phase=SeasonPhase.PRE_SEASON,
        )

        # Build game state
        self.game_state = GameState(
            config=config,
            season=season,
            teams=all_teams_dict,
            competitions=all_competitions,
            matches=all_matches_dict,
            human_team_id=result.human_team.id,
        )

    def _show_game_hub(self) -> None:
        """Show the main game dashboard."""
        if self.game_state is None:
            return

        def on_hub_result(action: str | None) -> None:
            if action == "squad":
                self._show_squad()
            elif action == "league":
                self._show_league_table()
            elif action == "calendar":
                self._show_calendar()
            elif action == "play_match":
                self._play_next_match()
            elif action == "save":
                self._save_game()
            elif action == "quit":
                self._show_main_menu()
            else:
                self._show_game_hub()

        self.push_screen(GameHubScreen(self.game_state), callback=on_hub_result)

    def _show_squad(self) -> None:
        """Show the squad management screen."""
        if self.game_state is None or self.game_state.human_team is None:
            return

        def on_back(_: None) -> None:
            self._show_game_hub()

        self.push_screen(SquadScreen(self.game_state.human_team), callback=on_back)

    def _show_league_table(self) -> None:
        """Show the league standings."""
        if self.game_state is None or self.game_state.human_team is None:
            return

        competition = self.game_state.current_competition
        if competition is None:
            return

        def on_back(_: None) -> None:
            self._show_game_hub()

        self.push_screen(
            LeagueTableScreen(competition, self.game_state.human_team),
            callback=on_back,
        )

    def _show_calendar(self) -> None:
        """Show the season calendar."""
        if self.game_state is None or self.game_state.human_team is None:
            return

        def on_back(_: None) -> None:
            self._show_game_hub()

        self.push_screen(
            CalendarScreen(
                self.game_state.season,
                self.game_state.matches,
                self.game_state.teams,
                self.game_state.human_team,
            ),
            callback=on_back,
        )

    def _play_next_match(self) -> None:
        """Play the next match day."""
        if self.game_state is None or self.game_state.human_team_id is None:
            self._show_game_hub()
            return

        # Find next match for human team
        human_match = self.game_state.get_next_match_for_team(
            self.game_state.human_team_id
        )
        if human_match is None:
            # Season is over — advance to next season
            advance_season(self.game_state)
            self.notify(
                t("notifications.season_completed") + " "
                + t("hub.season", year=self.game_state.season.year),
                title=t("notifications.end"),
            )
            self._show_game_hub()
            return

        # Get teams
        home_team = self.game_state.get_team(human_match.home_team_id)
        away_team = self.game_state.get_team(human_match.away_team_id)
        if home_team is None or away_team is None:
            self._show_game_hub()
            return

        competition = self.game_state.current_competition
        rules = competition.rules if competition else CompetitionRules()

        def on_match_result(result: Match | None) -> None:
            if result is None:
                self._show_game_hub()
                return
            self._process_match_day(human_match.match_day, result)
            self._show_game_hub()

        self.push_screen(
            LiveMatchScreen(
                home_team,
                away_team,
                rules,
                competition_name=competition.display_name if competition else "",
                match_day=human_match.match_day,
                match_date=human_match.match_date,
            ),
            callback=on_match_result,
        )

    def _get_competition_for_match(self, match: Match) -> Competition | None:
        """Find the competition that owns a given match."""
        comp_id = str(match.competition_id)
        return self.game_state.competitions.get(comp_id) if self.game_state else None

    def _process_match_day(self, match_day: int, human_result: Match) -> None:
        """Process all matches for a match day (simulate non-human matches).

        Supports multi-girone: each match is assigned to its own competition.
        """
        if self.game_state is None:
            return

        engine = MatchEngine()

        # Update human match result
        human_match_id = self._find_human_match_id(match_day)
        if human_match_id:
            self.game_state.matches[str(human_match_id)] = human_result
            comp = self._get_competition_for_match(human_result)
            if comp:
                update_standings(comp, human_result)

        # Simulate other matches on this day (all gironi)
        for md in self.game_state.season.calendar:
            if md.day_number != match_day:
                continue

            for mid in md.match_ids:
                match = self.game_state.matches.get(str(mid))
                if match is None or match.played:
                    continue

                home = self.game_state.get_team(match.home_team_id)
                away = self.game_state.get_team(match.away_team_id)
                if home is None or away is None:
                    continue

                comp = self._get_competition_for_match(match)
                rules = comp.rules if comp else CompetitionRules()

                result = engine.simulate(home, away, rules)
                result.id = match.id
                result.competition_id = match.competition_id
                result.match_day = match_day
                result.match_date = match.match_date
                self.game_state.matches[str(mid)] = result

                if comp:
                    update_standings(comp, result)

            md.played = True
            break

        # Update current_match_day for all affected competitions
        for comp in self.game_state.competitions.values():
            if any(str(mid) in {str(m) for m in comp.match_ids}
                   for md in self.game_state.season.calendar
                   if md.day_number == match_day
                   for mid in md.match_ids):
                comp.current_match_day = match_day

    def _find_human_match_id(self, match_day: int) -> UUID | None:
        """Find the human team's match ID for a given match day."""
        if self.game_state is None or self.game_state.human_team_id is None:
            return None

        for md in self.game_state.season.calendar:
            if md.day_number != match_day:
                continue
            for mid in md.match_ids:
                match = self.game_state.matches.get(str(mid))
                if match and (
                    match.home_team_id == self.game_state.human_team_id
                    or match.away_team_id == self.game_state.human_team_id
                ):
                    return mid
        return None

    def _save_game(self) -> None:
        """Show the save dialog and save the game."""
        if self.game_state is None:
            return

        team_name = ""
        if self.game_state.human_team:
            team_name = self.game_state.human_team.name

        def on_save_result(slot: str | None) -> None:
            if slot is None or self.game_state is None:
                self._show_game_hub()
                return
            save_game(self.game_state, slot)
            self.notify(
                t("notifications.game_saved", slot=slot),
                title=t("notifications.save_title"),
            )
            self._show_game_hub()

        self.push_screen(SaveGameScreen(default_name=team_name), callback=on_save_result)

    def _show_load_game(self) -> None:
        """Show the load game dialog."""

        def on_load_result(slot: str | None) -> None:
            if slot is None:
                self._show_main_menu()
                return
            state = load_game(slot)
            if state is None:
                self.notify(
                    t("notifications.save_not_found"),
                    title=t("save_game.error"),
                )
                self._show_main_menu()
                return
            self.game_state = state
            self.notify(
                t("notifications.game_loaded", slot=slot),
                title=t("notifications.load_title"),
            )
            self._show_game_hub()

        self.push_screen(LoadGameScreen(), callback=on_load_result)
