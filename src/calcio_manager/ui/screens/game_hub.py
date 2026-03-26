"""Game hub screen — central dashboard, CM 01/02 style."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.color import Color
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Static

from calcio_manager.data.player_art import COLS as _HUB_COLS
from calcio_manager.data.player_art import DATA as _HUB_DATA
from calcio_manager.data.player_art import ROWS as _HUB_ROWS
from calcio_manager.i18n import format_date, t
from calcio_manager.state.game_state import GameState
from calcio_manager.ui.block_font import render_block
from calcio_manager.ui.widgets.image_background import ImageBackground

# ---------------------------------------------------------------------------
# Italian colour names -> hex (shared with live_match)
# ---------------------------------------------------------------------------
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


class GameHubScreen(Screen[str]):
    """Central game dashboard — image background with floating panels."""

    BINDINGS = [
        ("r", "show_squad", t("hub.bindings.squad")),
        ("c", "show_calendar", t("hub.bindings.calendar")),
        ("l", "show_league", t("hub.bindings.league")),
        ("p", "play_match", t("hub.bindings.play_match")),
        ("s", "save_game", f"\u2502 {t('hub.bindings.save')}"),
        ("q", "quit_to_menu", t("hub.bindings.menu")),
    ]

    CSS = """
    GameHubScreen {
        layers: bg fg;
        overflow-y: hidden;
    }

    ImageBackground {
        layer: bg;
    }

    #hub-box {
        layer: fg;
        width: 100%;
        height: 1fr;
        overflow: hidden hidden;
    }

    #team-banner {
        height: 7;
        width: 100%;
        content-align: center middle;
        text-align: center;
        text-style: bold;
    }

    #panels-box {
        width: 100%;
        height: 1fr;
        layers: pbg pfg;
        overflow: hidden hidden;
    }

    #panels-bg {
        layer: pbg;
    }

    #panels-content {
        layer: pfg;
        width: 100%;
        height: 100%;
        padding: 0 2;
        overflow: hidden hidden;
    }

    #team-info {
        height: 3;
        width: 100%;
        content-align: center middle;
        text-align: center;
        color: $text-muted;
        background: $boost;
    }

    .info-row {
        height: 10;
        align: center top;
        margin: 1 2;
    }

    .info-panel {
        width: 1fr;
        max-width: 50;
        height: 100%;
        padding: 1 3;
        margin: 0 2;
        background: $boost;
        overflow: hidden;
    }

    .panel-title {
        height: 1;
        text-style: bold;
        text-align: center;
        color: #eab308;
    }

    .panel-body {
        height: auto;
    }

    Footer {
        layer: fg;
    }
    """

    def __init__(self, game_state: GameState) -> None:
        super().__init__()
        self.game_state = game_state

    def compose(self) -> ComposeResult:
        """Build the dashboard with transparent layout over image background."""
        yield ImageBackground(_HUB_DATA, _HUB_COLS, _HUB_ROWS)
        with Vertical(id="hub-box"):
            yield Static("", id="team-banner")
            with Vertical(id="panels-box"):
                yield ImageBackground(
                    _HUB_DATA, _HUB_COLS, _HUB_ROWS, id="panels-bg",
                )
                with Vertical(id="panels-content"):
                    yield Static("", id="team-info")
                    with Horizontal(classes="info-row"):
                        with Vertical(classes="info-panel"):
                            yield Static(t("hub.next_match"), classes="panel-title")
                            yield Static("", id="next-match-body", classes="panel-body")
                        with Vertical(classes="info-panel"):
                            yield Static(t("hub.standings"), classes="panel-title")
                            yield Static("", id="standing-body", classes="panel-body")
                    with Horizontal(classes="info-row"):
                        with Vertical(classes="info-panel"):
                            yield Static(t("hub.last_result"), classes="panel-title")
                            yield Static("", id="last-result-body", classes="panel-body")
                        with Vertical(classes="info-panel"):
                            yield Static(t("hub.squad"), classes="panel-title")
                            yield Static("", id="squad-summary-body", classes="panel-body")
        yield Footer()

    def on_mount(self) -> None:
        """Populate all dashboard widgets."""
        team = self.game_state.human_team
        if team is None:
            return

        self._populate_banner(team)
        self._populate_team_info(team)
        self._populate_next_match(team.id)
        self._populate_standing(team.id)
        self._populate_last_result(team.id)
        self._populate_squad_summary(team)

    def _populate_banner(self, team: object) -> None:
        """Set team banner with social colours and block letters."""
        from calcio_manager.models.team import Team
        if not isinstance(team, Team):
            return

        banner = self.query_one("#team-banner", Static)
        banner.update(render_block(team.name))
        bg_hex = _color_hex(team.colors[0])
        fg_hex = _auto_contrast(bg_hex)
        banner.styles.background = Color.parse(bg_hex)
        banner.styles.color = Color.parse(fg_hex)

    def _populate_team_info(self, team: object) -> None:
        """Fill the info line below the banner."""
        from calcio_manager.models.team import Team
        if not isinstance(team, Team):
            return

        parts: list[str] = []

        current_date = self.game_state.season.current_date
        if current_date:
            parts.append(format_date(current_date))

        parts.append(t("hub.season", year=self.game_state.season.year))

        comp = self.game_state.current_competition
        if comp:
            parts.append(t(f"divisions.{comp.division.value}"))

        day_num = self.game_state.season.current_match_day_number
        total_days = len(self.game_state.season.calendar)
        parts.append(t("hub.matchday", current=day_num, total=total_days))

        self.query_one("#team-info", Static).update(
            " \u2502 ".join(parts)
        )

    def _populate_next_match(self, team_id: object) -> None:
        """Fill the next-match panel."""
        from uuid import UUID

        tid = team_id if isinstance(team_id, UUID) else UUID(str(team_id))
        match = self.game_state.get_next_match_for_team(tid)
        widget = self.query_one("#next-match-body", Static)

        if match is None:
            widget.update(f"[bold]{t('hub.season_completed')}[/bold]")
            return

        opponent_id = (
            match.away_team_id
            if match.home_team_id == tid
            else match.home_team_id
        )
        opponent = self.game_state.get_team(opponent_id)
        opponent_name = opponent.name if opponent else "?"
        location = t("hub.home") if match.home_team_id == tid else t("hub.away")

        date_str = ""
        if match.match_date:
            date_str = f"\n{format_date(match.match_date)}"

        widget.update(
            f"[bold]{opponent_name}[/bold]\n"
            f"{location}{date_str}"
        )

    def _populate_standing(self, team_id: object) -> None:
        """Fill the standing panel."""
        comp = self.game_state.current_competition
        widget = self.query_one("#standing-body", Static)
        if comp is None:
            return

        sorted_standings = sorted(
            comp.standings, key=lambda r: (-r.points, -r.goal_difference),
        )
        for pos, row in enumerate(sorted_standings, 1):
            if row.team_id == team_id:
                widget.update(
                    f"[bold]{pos}\u00b0[/bold] \u2014 {row.points} {t('hub.points')}\n"
                    f"{row.wins}{t('standings_abbr.wins')}"
                    f" {row.wins_penalties}{t('standings_abbr.wins_pen')}"
                    f" {row.losses_penalties}{t('standings_abbr.losses_pen')}"
                    f" {row.losses}{t('standings_abbr.losses')}\n"
                    f"{t('standings_abbr.gf')} {row.goals_for}"
                    f" {t('standings_abbr.ga')} {row.goals_against}"
                    f" {t('standings_abbr.gd')} {row.goal_difference:+d}"
                )
                return

    def _populate_last_result(self, team_id: object) -> None:
        """Fill the last-result panel."""
        widget = self.query_one("#last-result-body", Static)

        for md in reversed(self.game_state.season.calendar):
            if not md.played:
                continue
            for mid in md.match_ids:
                match = self.game_state.get_match(mid)
                if match is None or not match.played:
                    continue
                if match.home_team_id != team_id and match.away_team_id != team_id:
                    continue

                home = self.game_state.get_team(match.home_team_id)
                away = self.game_state.get_team(match.away_team_id)
                h_name = home.name if home else "?"
                a_name = away.name if away else "?"
                h_goals = match.score.home_goals
                a_goals = match.score.away_goals
                widget.update(
                    f"{h_name}\n"
                    f"[bold]{h_goals} - {a_goals}[/bold]\n"
                    f"{a_name}"
                )
                return

        widget.update(t("hub.no_result"))

    def _populate_squad_summary(self, team: object) -> None:
        """Fill the squad summary panel."""
        from calcio_manager.models.team import Team
        if not isinstance(team, Team):
            return

        widget = self.query_one("#squad-summary-body", Static)
        total = len(team.squad)
        available = len(team.available_players)
        injured = sum(1 for p in team.squad if p.injury is not None)
        suspended = sum(1 for p in team.squad if p.suspended)
        avg_ovr = team.squad_average_overall

        widget.update(
            f"{t('hub.players', total=total, available=available)}\n"
            f"{t('hub.injured', count=injured)}\n"
            f"{t('hub.suspended', count=suspended)}\n"
            f"{t('hub.avg_ovr', value=f'{avg_ovr:.1f}')}"
        )

    # -- actions ----------------------------------------------------------

    def check_action(
        self, action: str, parameters: tuple[object, ...],
    ) -> bool | None:
        """Hide command palette."""
        if action == "command_palette":
            return None
        return True

    def action_show_squad(self) -> None:
        """Navigate to squad screen."""
        self.dismiss("squad")

    def action_show_calendar(self) -> None:
        """Navigate to calendar screen."""
        self.dismiss("calendar")

    def action_show_league(self) -> None:
        """Navigate to league table screen."""
        self.dismiss("league")

    def action_play_match(self) -> None:
        """Play next match."""
        self.dismiss("play_match")

    def action_save_game(self) -> None:
        """Save the game."""
        self.dismiss("save")

    def action_quit_to_menu(self) -> None:
        """Return to main menu."""
        self.dismiss("quit")
