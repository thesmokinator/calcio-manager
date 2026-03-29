"""Squad management screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.color import Color
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Static

from calcio_manager.i18n import t
from calcio_manager.models.enums import PlayerRole
from calcio_manager.models.team import Team
from calcio_manager.ui.block_font import render_block
from calcio_manager.ui.colors import auto_contrast, color_hex

# Role display order
_ROLE_ORDER = {
    PlayerRole.GK: 0, PlayerRole.DEF: 1,
    PlayerRole.MID: 2, PlayerRole.FWD: 3,
}


class SquadScreen(Screen[None]):
    """View and manage the team's squad."""

    BINDINGS = [
        ("escape", "back", t("squad_screen.back")),
    ]

    CSS = """
    SquadScreen {
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

    #squad-table {
        height: 1fr;
        margin: 1 2;
    }
    """

    def __init__(self, team: Team) -> None:
        super().__init__()
        self.team = team

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("", id="team-banner")
            yield Static("", id="screen-subtitle")
            yield DataTable(id="squad-table")
        yield Footer()

    def on_mount(self) -> None:
        """Style the banner and populate the table."""
        self._populate_banner()
        self._populate_subtitle()
        self._populate_table()

    def _populate_banner(self) -> None:
        """Set team banner with colours and block letters."""
        banner = self.query_one("#team-banner", Static)
        banner.update(render_block(self.team.name))
        bg_hex = color_hex(self.team.colors[0])
        fg_hex = auto_contrast(bg_hex)
        banner.styles.background = Color.parse(bg_hex)
        banner.styles.color = Color.parse(fg_hex)

    def _populate_subtitle(self) -> None:
        """Show squad header info."""
        subtitle = self.query_one("#screen-subtitle", Static)
        subtitle.update(
            t("squad_screen.header", team=self.team.name),
        )

    def _populate_table(self) -> None:
        """Populate the squad table."""
        table = self.query_one("#squad-table", DataTable)
        table.cursor_type = "row"
        table.add_columns(
            t("squad_screen.col_role"),
            t("squad_screen.col_name"),
            t("squad_screen.col_age"),
            t("squad_screen.col_ovr"),
            t("squad_screen.col_sho"),
            t("squad_screen.col_pas"),
            t("squad_screen.col_dri"),
            t("squad_screen.col_ftc"),
            t("squad_screen.col_pos"),
            t("squad_screen.col_dec"),
            t("squad_screen.col_pac"),
            t("squad_screen.col_sta"),
            t("squad_screen.col_str"),
            t("squad_screen.col_condition"),
            t("squad_screen.col_status"),
        )

        sorted_players = sorted(
            self.team.squad,
            key=lambda p: (_ROLE_ORDER.get(p.role, 99), -p.overall),
        )

        for player in sorted_players:
            attr = player.attributes
            condition_pct = f"{player.condition * 100:.0f}%"
            status = ""
            if player.injury:
                status = t(
                    "squad_screen.injured",
                    days=player.injury.days_remaining,
                )
            elif player.suspended:
                status = t("squad_screen.suspended")
            elif player.morale.value <= 2:
                status = t("squad_screen.low_morale")

            table.add_row(
                t(f"roles.{player.role.name}"),
                player.full_name,
                str(player.age),
                str(player.overall),
                str(attr.technical.finishing),
                str(attr.technical.passing),
                str(attr.technical.dribbling),
                str(attr.technical.first_touch),
                str(attr.mental.positioning),
                str(attr.mental.decisions),
                str(attr.physical.pace),
                str(attr.physical.stamina),
                str(attr.physical.strength),
                condition_pct,
                status,
            )

    def action_back(self) -> None:
        self.dismiss(None)
