"""Live match screen — CM 01/02 inspired layout."""

from __future__ import annotations

import asyncio
import random
from datetime import date
from uuid import UUID

from textual.app import ComposeResult
from textual.binding import Binding
from textual.color import Color
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Footer, RichLog, Static

from calcio_manager.engine.commentary import CommentaryEngine
from calcio_manager.engine.match import MatchEngine
from calcio_manager.engine.weather import generate_weather
from calcio_manager.i18n import format_date, t
from calcio_manager.models.config import CompetitionRules
from calcio_manager.models.enums import MatchEventType, TacticStyle
from calcio_manager.models.match import Match, MatchEvent
from calcio_manager.models.player import Player
from calcio_manager.models.team import Team

# ---------------------------------------------------------------------------
# Italian colour names -> hex (tuned for dark-background terminals)
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

# ---------------------------------------------------------------------------
# Event delays (seconds) — fixed speed, no user toggle
# ---------------------------------------------------------------------------
_EVENT_DELAYS: dict[MatchEventType, float] = {
    MatchEventType.GOAL: 3.5,
    MatchEventType.RED_CARD: 2.5,
    MatchEventType.SECOND_YELLOW: 2.5,
    MatchEventType.SHOT_POST: 2.0,
    MatchEventType.SHOT_SAVED: 1.5,
    MatchEventType.YELLOW_CARD: 1.5,
    MatchEventType.FOUL: 1.2,
    MatchEventType.CORNER: 1.2,
    MatchEventType.SHOT_WIDE: 1.2,
    MatchEventType.HALF_TIME: 2.5,
    MatchEventType.FULL_TIME: 2.5,
    MatchEventType.KICK_OFF: 2.0,
    MatchEventType.PENALTY_SHOOTOUT_START: 2.5,
    MatchEventType.PENALTY_SCORED: 2.0,
    MatchEventType.PENALTY_MISSED: 2.0,
    MatchEventType.PENALTY_SAVED: 2.0,
    MatchEventType.POSSESSION: 1.0,
}

# Events that appear in the team highlight columns
_KEY_EVENTS = frozenset({
    MatchEventType.GOAL,
    MatchEventType.SHOT_POST,
    MatchEventType.YELLOW_CARD,
    MatchEventType.RED_CARD,
    MatchEventType.SECOND_YELLOW,
    MatchEventType.PENALTY_SCORED,
    MatchEventType.PENALTY_MISSED,
    MatchEventType.PENALTY_SAVED,
})

# ---------------------------------------------------------------------------
# Referee pool
# ---------------------------------------------------------------------------
_REFEREES = [
    "M. Rossi", "G. Bianchi", "A. Colombo", "L. Ferrari", "P. Russo",
    "S. Romano", "D. Ricci", "F. Marino", "C. Greco", "R. Bruno",
    "V. Esposito", "N. De Luca", "T. Conti", "E. Galli", "B. Mancini",
]


# ---------------------------------------------------------------------------
# Colour helpers
# ---------------------------------------------------------------------------


def _color_hex(name: str) -> str:
    """Convert an Italian colour name to a hex code."""
    return _ITALIAN_TO_HEX.get(name, "#808080")


def _auto_contrast(bg_hex: str) -> str:
    """Return white or black hex for readable text on *bg_hex*."""
    r, g, b = int(bg_hex[1:3], 16), int(bg_hex[3:5], 16), int(bg_hex[5:7], 16)
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return "#ffffff" if luminance < 0.5 else "#1a1a1a"


def _team_text_color(team: Team) -> str:
    """Return the primary hex colour of a team (for commentary text)."""
    return _color_hex(team.colors[0])


# ---------------------------------------------------------------------------
# Block digits (3 rows x 3 cols) — "big font" for the scoreboard
# ---------------------------------------------------------------------------
_BIG_DIGITS: dict[str, list[str]] = {
    "0": ["\u2588\u2580\u2588", "\u2588 \u2588", "\u2580\u2580\u2580"],
    "1": [" \u2588 ", " \u2588 ", " \u2580 "],
    "2": ["\u2580\u2580\u2588", "\u2588\u2580\u2580", "\u2580\u2580\u2580"],
    "3": ["\u2580\u2580\u2588", " \u2580\u2588", "\u2580\u2580\u2580"],
    "4": ["\u2588 \u2588", "\u2580\u2580\u2588", "  \u2580"],
    "5": ["\u2588\u2580\u2580", "\u2580\u2580\u2588", "\u2580\u2580\u2580"],
    "6": ["\u2588\u2580\u2580", "\u2588\u2580\u2588", "\u2580\u2580\u2580"],
    "7": ["\u2580\u2580\u2588", "  \u2588", "  \u2580"],
    "8": ["\u2588\u2580\u2588", "\u2588\u2580\u2588", "\u2580\u2580\u2580"],
    "9": ["\u2588\u2580\u2588", "\u2580\u2580\u2588", "  \u2580"],
}


def _big_number(n: int) -> str:
    """Render an integer as a 3-row block digit string."""
    digits = str(n)
    rows: list[str] = ["", "", ""]
    for i, ch in enumerate(digits):
        glyph = _BIG_DIGITS.get(ch, [" ? ", " ? ", " ? "])
        sep = " " if i > 0 else ""
        for r in range(3):
            rows[r] += sep + glyph[r]
    return "\n".join(rows)


# ---------------------------------------------------------------------------
# Screen
# ---------------------------------------------------------------------------

class LiveMatchScreen(Screen[Match]):
    """Watch a match unfold with real-time commentary.

    Layout inspired by CM 01/02:
    - Scoreboard: coloured team bars + score
    - Time / phase indicator
    - Date and competition info
    - Two columns for key events (goals, cards, penalties)
    - Referee / attendance / weather bar
    - Possession bar (graphical, team colours)
    - Commentary line (shows venue when idle)
    """

    BINDINGS = [
        Binding("space", "match_action", t("match.bindings.start")),
        Binding("t", "change_tactic", t("match.bindings.tactics")),
        Binding("escape", "dismiss_result", t("match.bindings.continue")),
    ]

    CSS = """
    LiveMatchScreen {
        layout: vertical;
    }

    #scoreboard-bar {
        height: 5;
    }

    .team-name {
        width: 1fr;
        height: 100%;
        content-align: center middle;
        text-align: center;
        text-style: bold;
    }

    .team-score {
        width: 10;
        height: 100%;
        content-align: center middle;
        text-align: center;
        text-style: bold;
        background: $surface-darken-2;
    }

    #time-display {
        height: 3;
        content-align: center middle;
        text-align: center;
        text-style: bold italic;
        color: $success;
        background: $surface-darken-1;
    }

    #match-info-bar {
        height: 3;
    }

    .match-info-cell {
        width: 1fr;
        height: 100%;
        content-align: center middle;
        color: $text-muted;
        padding: 0 2;
        background: $surface-darken-2;
    }

    #match-date {
        content-align: left middle;
    }

    #match-competition {
        content-align: right middle;
    }

    #events-area {
        height: 1fr;
        margin: 0 2;
    }

    .events-log {
        width: 1fr;
        height: 1fr;
        padding: 1 2;
        margin: 0 1;
        scrollbar-size-vertical: 0;
    }

    #bottom-info {
        height: 3;
        content-align: center middle;
        text-align: center;
        color: $text-muted;
        padding: 0 2;
    }

    #possession-bar {
        height: 3;
        content-align: center middle;
        text-align: center;
        padding: 0 4;
    }

    #commentary {
        height: 5;
        content-align: center middle;
        text-align: center;
        padding: 0 2;
        background: $surface-darken-1;
        margin: 0 2;
    }
    """

    def __init__(
        self,
        home_team: Team,
        away_team: Team,
        rules: CompetitionRules,
        *,
        competition_name: str = "",
        match_day: int = 0,
        match_date: date | None = None,
    ) -> None:
        super().__init__()
        self.home_team = home_team
        self.away_team = away_team
        self.rules = rules
        self.commentary = CommentaryEngine()
        self._result: Match | None = None
        self._match_started = False
        self._paused = False
        self._match_finished = False
        self._waiting_phase = ""
        self._home_goals = 0
        self._away_goals = 0
        self._current_minute = 0
        self._half_label = t("match.first_half")
        self._home_possession = 50.0
        self._away_possession = 50.0
        self._home_poss_count = 0
        self._away_poss_count = 0
        self._home_shots = 0
        self._away_shots = 0
        self._home_fouls = 0
        self._away_fouls = 0
        self._home_corners = 0
        self._away_corners = 0
        self._players: dict[UUID, Player] = {}

        # Pre-build colour helpers
        self._home_text_color = _team_text_color(home_team)
        self._away_text_color = _team_text_color(away_team)
        self._home_color_hex = _color_hex(home_team.colors[0])
        self._away_color_hex = _color_hex(away_team.colors[0])

        # Match context
        self._competition_name = competition_name
        self._match_day = match_day
        self._match_date = match_date
        self._venue = t(
            "match.province_of",
            city=home_team.city,
            province=home_team.province,
        )
        self._attendance = random.randint(20, 200)

        # Generate referee and weather
        self._referee = random.choice(_REFEREES)
        month = match_date.month if match_date else 9
        weather = generate_weather(month)
        self._weather_icon = weather.icon
        self._weather_label = t(f"weather.{weather.key}")
        self._temperature = weather.temperature

        # Build player lookup
        for player in home_team.squad + away_team.squad:
            self._players[player.id] = player

    # -- compose ----------------------------------------------------------

    def compose(self) -> ComposeResult:
        """Build the CM 01/02 inspired match layout."""
        with Horizontal(id="scoreboard-bar"):
            yield Static(
                self.home_team.name.upper(),
                id="home-name", classes="team-name",
            )
            yield Static(_big_number(0), id="home-score", classes="team-score")
            yield Static(_big_number(0), id="away-score", classes="team-score")
            yield Static(
                self.away_team.name.upper(),
                id="away-name", classes="team-name",
            )
        yield Static("", id="time-display")
        with Horizontal(id="match-info-bar"):
            yield Static("", id="match-date", classes="match-info-cell")
            yield Static("", id="match-competition", classes="match-info-cell")
        with Horizontal(id="events-area"):
            home_log = RichLog(
                id="home-events", highlight=False, markup=True,
                classes="events-log",
            )
            home_log.can_focus = False
            yield home_log
            away_log = RichLog(
                id="away-events", highlight=False, markup=True,
                classes="events-log",
            )
            away_log.can_focus = False
            yield away_log
        yield Static("", id="bottom-info")
        yield Static("", id="possession-bar")
        yield Static("", id="commentary")
        yield Footer()

    def on_mount(self) -> None:
        """Initialise displays and start match simulation."""
        # Apply team colours to scoreboard name bars
        home_bg = self._home_color_hex
        home_fg = _auto_contrast(home_bg)
        home_widget = self.query_one("#home-name", Static)
        home_widget.styles.background = Color.parse(home_bg)
        home_widget.styles.color = Color.parse(home_fg)

        away_bg = self._away_color_hex
        away_fg = _auto_contrast(away_bg)
        away_widget = self.query_one("#away-name", Static)
        away_widget.styles.background = Color.parse(away_bg)
        away_widget.styles.color = Color.parse(away_fg)

        self._update_scoreboard()
        self._update_match_info()
        self._update_bottom_info()
        self._update_possession_bar()

        # Venue as default commentary (idle state, like CM 01/02)
        self.query_one("#commentary", Static).update(
            f"[dim]{self._venue}[/dim]",
        )

    # -- simulation loop --------------------------------------------------

    async def _simulate_match(self) -> None:
        """Run the match engine and feed events into the UI."""
        engine = MatchEngine()
        commentary_widget = self.query_one("#commentary", Static)
        home_log = self.query_one("#home-events", RichLog)
        away_log = self.query_one("#away-events", RichLog)

        events_queue: asyncio.Queue[MatchEvent] = asyncio.Queue()

        def on_event(event: MatchEvent) -> None:
            events_queue.put_nowait(event)

        engine.add_listener(on_event)

        loop = asyncio.get_event_loop()
        match_future = loop.run_in_executor(
            None, engine.simulate, self.home_team, self.away_team, self.rules,
        )

        last_possession_minute = -1

        while not match_future.done() or not events_queue.empty():
            # Pause support
            while self._paused:
                await asyncio.sleep(0.1)

            try:
                event = events_queue.get_nowait()
            except asyncio.QueueEmpty:
                await asyncio.sleep(0.05)
                continue

            self._current_minute = event.minute
            self._update_half_label(event)
            self._track_stats(event)

            # Filter possession: show only once per minute and only if
            # no action events are queued (action events are more interesting).
            if event.event_type == MatchEventType.POSSESSION:
                if event.minute == last_possession_minute or not events_queue.empty():
                    last_possession_minute = event.minute
                    self._update_scoreboard()
                    self._update_possession_bar()
                    continue
                last_possession_minute = event.minute

            # -- single commentary line -----------------------------------
            if event.event_type == MatchEventType.POSSESSION:
                # Idle state: show venue (like CM 01/02)
                commentary_widget.update(f"[dim]{self._venue}[/dim]")
            else:
                text = self.commentary.generate(
                    event=event,
                    home_team=self.home_team,
                    away_team=self.away_team,
                    home_goals=self._home_goals,
                    away_goals=self._away_goals,
                    players=self._players,
                )
                if text:
                    self._update_commentary(commentary_widget, event, text)

            # -- key events -> team columns --------------------------------
            if event.event_type in _KEY_EVENTS:
                self._write_key_event(event, home_log, away_log)

            self._update_scoreboard()
            self._update_possession_bar()

            # -- pacing ---------------------------------------------------
            delay = _EVENT_DELAYS.get(event.event_type, 1.0)
            if delay > 0:
                await asyncio.sleep(delay)

            # -- phase transitions: wait for user -------------------------
            if event.event_type == MatchEventType.HALF_TIME:
                self._waiting_phase = "second_half"
                self._update_space_label(t("match.bindings.second_half"))
                commentary_widget.update(f"[dim]{self._venue}[/dim]")
                while self._waiting_phase:
                    await asyncio.sleep(0.1)
            elif event.event_type == MatchEventType.PENALTY_SHOOTOUT_START:
                self._waiting_phase = "penalties"
                self._update_space_label(t("match.bindings.penalties"))
                commentary_widget.update(f"[dim]{self._venue}[/dim]")
                while self._waiting_phase:
                    await asyncio.sleep(0.1)

        # -- finalise -----------------------------------------------------
        self._result = await asyncio.wrap_future(match_future)  # type: ignore[arg-type]
        self._half_label = t("match.full_time")
        self._match_finished = True
        self._update_scoreboard()
        self._update_possession_bar()
        # Hide space, show escape "Continue"
        self.refresh_bindings()

        if self._result:
            self._show_final_summary(commentary_widget)

    # -- stat tracking ----------------------------------------------------

    def _track_stats(self, event: MatchEvent) -> None:
        """Update running statistics from an event."""
        etype = event.event_type
        is_home = event.team_id == self.home_team.id

        if etype == MatchEventType.GOAL:
            if is_home:
                self._home_goals += 1
            else:
                self._away_goals += 1

        if etype in (
            MatchEventType.SHOT_SAVED, MatchEventType.SHOT_WIDE,
            MatchEventType.SHOT_POST, MatchEventType.GOAL,
        ):
            if is_home:
                self._home_shots += 1
            else:
                self._away_shots += 1

        if etype == MatchEventType.FOUL:
            if is_home:
                self._home_fouls += 1
            else:
                self._away_fouls += 1

        if etype == MatchEventType.CORNER:
            if is_home:
                self._home_corners += 1
            else:
                self._away_corners += 1

        if etype == MatchEventType.POSSESSION:
            if is_home:
                self._home_poss_count += 1
            else:
                self._away_poss_count += 1
            total = self._home_poss_count + self._away_poss_count
            self._home_possession = (self._home_poss_count / total) * 100
            self._away_possession = 100 - self._home_possession

    # -- display helpers --------------------------------------------------

    def _update_half_label(self, event: MatchEvent) -> None:
        """Keep the half / phase label in sync with game progress."""
        etype = event.event_type
        if etype == MatchEventType.HALF_TIME:
            self._half_label = t("match.half_time")
        elif etype == MatchEventType.FULL_TIME:
            self._half_label = t("match.full_time")
        elif etype == MatchEventType.PENALTY_SHOOTOUT_START:
            self._half_label = t("match.penalties")
        elif (
            self._half_label == t("match.half_time")
            and self._current_minute > self.rules.half_duration_minutes
        ):
            self._half_label = t("match.second_half")

    def _update_commentary(
        self, widget: Static, event: MatchEvent, text: str,
    ) -> None:
        """Replace the single commentary line (CM 01/02 style)."""
        etype = event.event_type

        if etype in (
            MatchEventType.HALF_TIME, MatchEventType.FULL_TIME,
            MatchEventType.PENALTY_SHOOTOUT_START,
        ):
            widget.update(f"[bold]{text}[/bold]")
            return

        team_color = (
            self._home_text_color
            if event.team_id == self.home_team.id
            else self._away_text_color
        )

        if etype == MatchEventType.GOAL:
            widget.update(f"[bold blink {team_color}]\u26bd {text}[/]")
        elif etype in (MatchEventType.RED_CARD, MatchEventType.SECOND_YELLOW):
            widget.update(f"[bold red]\U0001f7e5 {text}[/bold red]")
        elif etype == MatchEventType.YELLOW_CARD:
            widget.update(f"[yellow]\U0001f7e8 {text}[/yellow]")
        elif etype == MatchEventType.SHOT_POST:
            widget.update(f"[bold italic]{text}[/bold italic]")
        else:
            widget.update(text)

    def _write_key_event(
        self, event: MatchEvent,
        home_log: RichLog, away_log: RichLog,
    ) -> None:
        """Write a key event (goal, card, penalty) to the team's column."""
        player_name = ""
        if event.player_id:
            player = self._players.get(event.player_id)
            if player:
                player_name = player.short_name

        is_home = event.team_id == self.home_team.id
        log = home_log if is_home else away_log
        team_color = self._home_text_color if is_home else self._away_text_color

        etype = event.event_type
        pen = t("match.pen_abbr")
        if etype == MatchEventType.GOAL:
            assist = ""
            if event.assist_player_id:
                ap = self._players.get(event.assist_player_id)
                if ap:
                    assist = f" ({ap.short_name})"
            log.write(
                f"[bold {team_color}]{event.minute}' \u26bd {player_name}{assist}[/]",
            )
        elif etype == MatchEventType.YELLOW_CARD:
            log.write(f"[yellow]{event.minute}' \U0001f7e8 {player_name}[/yellow]")
        elif etype in (MatchEventType.RED_CARD, MatchEventType.SECOND_YELLOW):
            log.write(
                f"[bold red]{event.minute}' \U0001f7e5 {player_name}[/bold red]",
            )
        elif etype == MatchEventType.PENALTY_SCORED:
            log.write(
                f"[bold {team_color}]{event.minute}' \u26bd"
                f" {player_name} ({pen})[/]",
            )
        elif etype == MatchEventType.SHOT_POST:
            log.write(
                f"[dim]{event.minute}' \u2503 {player_name}[/dim]",
            )
        elif etype in (MatchEventType.PENALTY_MISSED, MatchEventType.PENALTY_SAVED):
            log.write(
                f"[bold red]{event.minute}' \u2718 {player_name} ({pen})[/bold red]",
            )

    def _show_final_summary(self, widget: Static) -> None:
        """Show venue in the commentary area at end of match."""
        widget.update(f"[dim]{self._venue}[/dim]")

    def _update_scoreboard(self) -> None:
        """Update the scoreboard score and clock."""
        self.query_one("#home-score", Static).update(_big_number(self._home_goals))
        self.query_one("#away-score", Static).update(_big_number(self._away_goals))
        time_display = self.query_one("#time-display", Static)
        if self._paused:
            time_display.update(
                f"\u23f8 {t('match.pause')} \u2014 {self._current_minute}'",
            )
        else:
            time_display.update(
                f"{self._current_minute}'  \u2014  {self._half_label}",
            )

    def _update_match_info(self) -> None:
        """Show date and competition info below the scoreboard."""
        date_w = self.query_one("#match-date", Static)
        comp_w = self.query_one("#match-competition", Static)
        if self._match_date:
            date_w.update(format_date(self._match_date))
        if self._competition_name:
            label = self._competition_name
            if self._match_day > 0:
                label += f"  |  {t('match.matchday', day=self._match_day)}"
            comp_w.update(label)

    def _update_bottom_info(self) -> None:
        """Show referee, attendance and weather below the events."""
        info = self.query_one("#bottom-info", Static)
        info.update(
            f"{t('match.referee')}: {self._referee}"
            f"  |  {t('match.attendance')}: {self._attendance}"
            f"  |  {self._weather_icon} {self._weather_label},"
            f" {self._temperature}\u00b0C"
        )

    def _update_possession_bar(self) -> None:
        """Update the graphical possession bar with team colours."""
        bar_widget = self.query_one("#possession-bar", Static)
        bar_width = 80
        home_w = round(self._home_possession / 100 * bar_width)
        away_w = bar_width - home_w
        home_hex = self._home_color_hex
        away_hex = self._away_color_hex
        bar_widget.update(
            f" {self._home_possession:.0f}%  "
            f"[{home_hex}]{'\u2588' * home_w}[/]"
            f"[{away_hex}]{'\u2588' * away_w}[/]"
            f"  {self._away_possession:.0f}% "
        )

    # -- actions ----------------------------------------------------------

    def check_action(
        self, action: str, parameters: tuple[object, ...],
    ) -> bool | None:
        """Control binding visibility based on match state."""
        if action == "command_palette":
            return None
        if action == "dismiss_result":
            return True if self._match_finished else None
        if action == "match_action":
            return None if self._match_finished else True
        if action == "change_tactic":
            return (
                True
                if self._match_started and not self._match_finished
                else None
            )
        return True

    def _update_space_label(self, label: str) -> None:
        """Update the space binding description in the footer."""
        self._bindings.key_to_bindings["space"] = [
            Binding(key="space", action="match_action", description=label),
        ]
        self.refresh_bindings()

    def action_match_action(self) -> None:
        """Unified space-bar handler — dispatches based on match state."""
        if not self._match_started:
            self._match_started = True
            self._update_space_label(t("match.bindings.pause"))
            self.run_worker(self._simulate_match(), exclusive=True)
        elif self._waiting_phase in ("second_half", "penalties"):
            self._waiting_phase = ""
            self._update_space_label(t("match.bindings.pause"))
        elif not self._match_finished:
            self._paused = not self._paused
            if self._paused:
                self._update_space_label(t("match.bindings.resume"))
            else:
                self._update_space_label(t("match.bindings.pause"))
            self._update_scoreboard()

    def action_change_tactic(self) -> None:
        """Open the tactic selector modal."""
        if not self._match_started or self._match_finished:
            return

        from calcio_manager.ui.screens.tactic_modal import TacticModal

        def on_tactic(result: TacticStyle | None) -> None:
            if result is not None and result != self.home_team.tactic:
                self.home_team.tactic = result
                label = t(f"tactics.{result.value}")
                self.notify(label, title=t("match.bindings.tactics"))

        self.app.push_screen(TacticModal(self.home_team.tactic), callback=on_tactic)

    def action_dismiss_result(self) -> None:
        """Dismiss screen — only works after the match is over."""
        if self._result is not None:
            self.dismiss(self._result)
