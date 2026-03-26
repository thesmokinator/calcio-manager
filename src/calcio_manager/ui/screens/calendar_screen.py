"""Calendar / fixture list screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.color import Color
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Static

from calcio_manager.i18n import format_date, t
from calcio_manager.models.match import Match
from calcio_manager.models.season import Season
from calcio_manager.models.team import Team
from calcio_manager.ui.block_font import render_block

_ITALIAN_TO_HEX: dict[str, str] = {
    "bianco": "#d4d4d4",
    "nero": "#3a3a3a",
    "rosso": "#dc2626",
    "blu": "#2563eb",
    "giallo": "#eab308",
    "verde": "#16a34a",
    "azzurro": "#38bdf8",
    "arancione": "#f97316",
    "viola": "#a855f7",
    "grigio": "#9ca3af",
}


def _color_hex(name: str) -> str:
    """Convert an Italian colour name to a hex code."""
    return _ITALIAN_TO_HEX.get(name, "#808080")


def _auto_contrast(bg_hex: str) -> str:
    """Return white or black hex for readable text on *bg_hex*."""
    r, g, b = int(bg_hex[1:3], 16), int(bg_hex[3:5], 16), int(bg_hex[5:7], 16)
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return "#ffffff" if luminance < 0.5 else "#1a1a1a"


class CalendarScreen(Screen[None]):
    """Display the season calendar with fixtures and results."""

    BINDINGS = [
        ("escape", "back", t("calendar_screen.back")),
    ]

    CSS = """
    CalendarScreen {
        layout: vertical;
    }

    #team-banner {
        height: 7;
        width: 100%;
        content-align: center middle;
        text-align: center;
        text-style: bold;
    }

    #screen-subtitle {
        height: 3;
        width: 100%;
        content-align: center middle;
        text-align: center;
        color: $text-muted;
        background: $boost;
    }

    #calendar-table {
        height: 1fr;
        margin: 1 2;
    }
    """

    def __init__(
        self,
        season: Season,
        matches: dict[str, Match],
        teams: dict[str, Team],
        human_team: Team,
    ) -> None:
        super().__init__()
        self.season = season
        self.matches = matches
        self.teams = teams
        self.human_team = human_team

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("", id="team-banner")
            yield Static("", id="screen-subtitle")
            yield DataTable(id="calendar-table")
        yield Footer()

    def on_mount(self) -> None:
        """Populate the banner and calendar table."""
        self._populate_banner()
        self._populate_subtitle()
        self._populate_table()

    def _populate_banner(self) -> None:
        """Set team banner with colours and block letters."""
        banner = self.query_one("#team-banner", Static)
        banner.update(render_block(self.human_team.name))
        bg_hex = _color_hex(self.human_team.colors[0])
        fg_hex = _auto_contrast(bg_hex)
        banner.styles.background = Color.parse(bg_hex)
        banner.styles.color = Color.parse(fg_hex)

    def _populate_subtitle(self) -> None:
        """Show calendar header info."""
        subtitle = self.query_one("#screen-subtitle", Static)
        subtitle.update(
            t("calendar_screen.header", year=self.season.year),
        )

    def _populate_table(self) -> None:
        """Populate the calendar table."""
        table = self.query_one("#calendar-table", DataTable)
        table.cursor_type = "row"
        table.add_columns(
            t("calendar_screen.col_matchday"),
            t("calendar_screen.col_date"),
            t("calendar_screen.col_home"),
            "",
            t("calendar_screen.col_away"),
            t("calendar_screen.col_result"),
        )

        for md in self.season.calendar:
            for mid in md.match_ids:
                match = self.matches.get(str(mid))
                if match is None:
                    continue

                if (
                    match.home_team_id == self.human_team.id
                    or match.away_team_id == self.human_team.id
                ):
                    home = self.teams.get(str(match.home_team_id))
                    away = self.teams.get(str(match.away_team_id))
                    home_name = home.name if home else "?"
                    away_name = away.name if away else "?"
                    date_str = (
                        format_date(md.date) if md.date else "?"
                    )

                    result = match.score.display if match.played else "\u2014"

                    table.add_row(
                        str(md.day_number),
                        date_str,
                        home_name,
                        "vs",
                        away_name,
                        result,
                    )
                    break

    def action_back(self) -> None:
        """Return to game hub."""
        self.dismiss(None)
