"""New game setup screen — team selection."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, DataTable, Footer, Header, Label

from calcio_manager.engine.player_gen import generate_league_teams
from calcio_manager.i18n import t
from calcio_manager.models.team import Team


class NewGameResult:
    """Result of the new game screen: selected team + all generated teams."""

    def __init__(self, selected: Team, all_teams: list[Team]) -> None:
        self.selected = selected
        self.all_teams = all_teams


class NewGameScreen(Screen[NewGameResult | None]):
    """Screen for starting a new game: select your team."""

    BINDINGS = [
        ("escape", "cancel", t("new_game.back")),
        ("enter", "select", t("new_game.select_team")),
    ]

    CSS = """
    NewGameScreen {
        layout: vertical;
    }

    #team-list-container {
        height: 1fr;
        margin: 1 2;
    }

    #instructions {
        text-align: center;
        color: $text-muted;
        padding: 1;
    }

    #action-bar {
        height: 3;
        align: center middle;
        padding: 0 2;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._teams: list[Team] = []

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        yield Label(t("new_game.instructions"), id="instructions")
        with Vertical(id="team-list-container"):
            yield DataTable(id="team-table")
        with Vertical(id="action-bar"):
            yield Button(t("new_game.start"), id="start", variant="primary")
        yield Footer()

    def on_mount(self) -> None:
        """Generate teams and populate the table."""
        self._teams = generate_league_teams(
            num_teams=8,
            province="varese",
        )

        table = self.query_one("#team-table", DataTable)
        table.cursor_type = "row"
        table.add_columns(
            t("new_game.col_team"),
            t("new_game.col_city"),
            t("new_game.col_formation"),
            t("new_game.col_tactic"),
            t("new_game.col_squad"),
            t("new_game.col_average"),
        )

        for team in self._teams:
            table.add_row(
                team.name,
                team.city,
                team.formation.name,
                t(f"tactics.{team.tactic.value}"),
                str(len(team.squad)),
                f"{team.squad_average_overall:.1f}",
            )

    def action_cancel(self) -> None:
        """Return to main menu."""
        self.dismiss(None)

    def action_select(self) -> None:
        """Select the highlighted team."""
        table = self.query_one("#team-table", DataTable)
        if table.cursor_row is not None and 0 <= table.cursor_row < len(self._teams):
            selected = self._teams[table.cursor_row]
            selected.is_human = True
            self.dismiss(NewGameResult(selected, self._teams))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle start button."""
        if event.button.id == "start":
            self.action_select()

    @property
    def teams(self) -> list[Team]:
        """Expose generated teams for the app to use."""
        return self._teams
