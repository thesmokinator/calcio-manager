"""Main Textual application for Calcio Manager."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from textual.app import App

from calcio_manager.engine.calendar import generate_match_schedule, generate_round_robin
from calcio_manager.engine.competition import initialize_standings, update_standings
from calcio_manager.engine.match import MatchEngine
from calcio_manager.i18n import t
from calcio_manager.models.competition import Competition
from calcio_manager.models.config import CompetitionRules, GameConfig
from calcio_manager.models.enums import AgeCategory, CompetitionType, Division, GameFormat
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
        """Show team selection screen and initialize a new game."""

        def on_team_selected(result: NewGameResult | None) -> None:
            if result is None:
                self._show_main_menu()
                return

            self._initialize_game(result.selected, result.all_teams)
            self._show_game_hub()

        self.push_screen(NewGameScreen(), callback=on_team_selected)

    def _initialize_game(self, human_team: Team, all_teams: list[Team]) -> None:
        """Set up a new game with generated teams and schedule."""
        config = GameConfig(
            province="Varese",
            region="Lombardia",
            num_groups=1,
            teams_per_group=len(all_teams),
        )

        rules = CompetitionRules.for_category(AgeCategory.OPEN, GameFormat.C7)

        # Create competition
        competition = Competition(
            name=t(
                "competition.name_template",
                province="Varese",
                division="Serie Oro",
            ),
            format=GameFormat.C7,
            category=AgeCategory.OPEN,
            competition_type=CompetitionType.LEAGUE,
            division=Division.SERIE_ORO,
            province="Varese",
            region="Lombardia",
            team_ids=[team.id for team in all_teams],
            rules=rules,
        )

        # Initialize standings
        team_names = {team.id: team.name for team in all_teams}
        initialize_standings(competition, team_names)

        # Generate schedule (andata e ritorno)
        rounds = generate_round_robin([team.id for team in all_teams], home_and_away=True)
        all_matches, match_days = generate_match_schedule(
            rounds, competition.id
        )

        competition.total_match_days = len(match_days)
        competition.match_ids = [m.id for m in all_matches]

        # Create season
        season = Season(
            year=config.season_year,
            competition_ids=[competition.id],
            calendar=match_days,
        )

        # Build game state
        self.game_state = GameState(
            config=config,
            season=season,
            teams={str(team.id): team for team in all_teams},
            competitions={str(competition.id): competition},
            matches={str(m.id): m for m in all_matches},
            human_team_id=human_team.id,
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
            self.notify(
                t("notifications.season_completed"),
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
                competition_name=competition.name if competition else "",
                match_day=human_match.match_day,
                match_date=human_match.match_date,
            ),
            callback=on_match_result,
        )

    def _process_match_day(self, match_day: int, human_result: Match) -> None:
        """Process all matches for a match day (simulate non-human matches)."""
        if self.game_state is None:
            return

        competition = self.game_state.current_competition
        if competition is None:
            return

        engine = MatchEngine()

        # Update human match result
        human_match_id = self._find_human_match_id(match_day)
        if human_match_id:
            self.game_state.matches[str(human_match_id)] = human_result
            update_standings(competition, human_result)

        # Simulate other matches on this day
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

                result = engine.simulate(home, away, competition.rules)
                result.id = match.id
                result.competition_id = competition.id
                result.match_day = match_day
                result.match_date = match.match_date
                self.game_state.matches[str(mid)] = result
                update_standings(competition, result)

            md.played = True
            break

        competition.current_match_day = match_day

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
