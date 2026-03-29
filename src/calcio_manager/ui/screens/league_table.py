"""League standings screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.color import Color
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Label, Static

from calcio_manager.engine.competition import sort_standings
from calcio_manager.i18n import t
from calcio_manager.models.competition import Competition
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


class LeagueTableScreen(Screen[None]):
    """Display the league standings with CSI points system."""

    BINDINGS = [
        ("escape", "back", t("league.back")),
    ]

    CSS = """
    LeagueTableScreen {
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

    #standings-table {
        height: 1fr;
        margin: 1 2;
    }

    #legend {
        text-align: center;
        color: $text-muted;
        padding: 0 2 1 2;
        height: 2;
    }
    """

    def __init__(self, competition: Competition, human_team: Team) -> None:
        super().__init__()
        self.competition = competition
        self.human_team = human_team

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("", id="team-banner")
            yield Static("", id="screen-subtitle")
            yield DataTable(id="standings-table")
            yield Label(t("league.legend"), id="legend")
        yield Footer()

    def on_mount(self) -> None:
        """Populate the banner and standings table."""
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
        """Show competition name as subtitle."""
        subtitle = self.query_one("#screen-subtitle", Static)
        subtitle.update(
            t("league.header", name=self.competition.display_name),
        )

    def _populate_table(self) -> None:
        """Populate the standings table."""
        table = self.query_one("#standings-table", DataTable)
        table.cursor_type = "row"
        table.add_columns(
            t("league.col_pos"),
            t("league.col_team"),
            t("league.col_played"),
            t("league.col_wins"),
            t("league.col_wins_pen"),
            t("league.col_losses_pen"),
            t("league.col_losses"),
            t("league.col_gf"),
            t("league.col_ga"),
            t("league.col_gd"),
            t("league.col_pts"),
        )

        sorted_rows = sort_standings(self.competition.standings)

        for pos, row in enumerate(sorted_rows, 1):
            table.add_row(
                str(pos),
                row.team_name,
                str(row.played),
                str(row.wins),
                str(row.wins_penalties),
                str(row.losses_penalties),
                str(row.losses),
                str(row.goals_for),
                str(row.goals_against),
                f"{row.goal_difference:+d}",
                str(row.points),
            )

    def action_back(self) -> None:
        """Return to game hub."""
        self.dismiss(None)
