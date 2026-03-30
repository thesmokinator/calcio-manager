"""New game wizard — multi-step career setup."""

from __future__ import annotations

import re
import string
import unicodedata

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.screen import ModalScreen, Screen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Input,
    Label,
    Static,
)

from calcio_manager.data.comuni import (
    get_comuni,
    get_provinces,
    get_region_for_province,
    get_regions,
)
from calcio_manager.engine.player_gen import generate_team, generate_tournament_teams
from calcio_manager.engine.season_manager import compute_season_year, default_start_year
from calcio_manager.engine.tournament import (
    calculate_gironi_structure,
    generate_gironi,
    select_tournament_comuni,
)
from calcio_manager.i18n import t
from calcio_manager.models.team import Team
from calcio_manager.ui.colors import ITALIAN_TO_HEX, auto_contrast, color_hex

# All available color names for team customization
_COLOR_NAMES = list(ITALIAN_TO_HEX.keys())

_HEX_PATTERN = re.compile(r"^#[0-9a-fA-F]{6}$")


def _safe_id(text: str) -> str:
    """Convert any text to a valid Textual CSS identifier."""
    nfkd = unicodedata.normalize("NFKD", text)
    ascii_text = nfkd.encode("ascii", "ignore").decode("ascii")
    return "".join(c if c.isalnum() else "_" for c in ascii_text)


def _color_label(color: str) -> str:
    """Return a display label for a color (named or custom hex)."""
    if color.startswith("#"):
        return color.upper()
    return t(f"colors.{color}")


def _color_to_hex(color: str) -> str:
    """Resolve a color (named or custom hex) to a hex code."""
    if color.startswith("#"):
        return color
    return color_hex(color)


_STEP_TITLES = {
    1: "wizard.step_region",
    2: "wizard.step_province",
    3: "wizard.step_comune",
    4: "wizard.step_customize",
    5: "wizard.step_preview",
}


# ---------------------------------------------------------------------------
# Color picker modal
# ---------------------------------------------------------------------------

class ColorPickerModal(ModalScreen[str | None]):
    """Modal dialog for choosing a team color."""

    BINDINGS = [
        ("escape", "cancel", t("wizard.back")),
    ]

    CSS = """
    ColorPickerModal {
        align: center middle;
    }

    #color-dialog {
        width: 70;
        height: auto;
        max-height: 80%;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }

    #color-dialog-title {
        text-align: center;
        text-style: bold;
        padding: 0 0 1 0;
    }

    #color-palette {
        layout: grid;
        grid-size: 5;
        grid-gutter: 1;
        grid-rows: auto;
        height: auto;
        width: 100%;
    }

    .palette-btn {
        width: 100%;
        height: 3;
        content-align: center middle;
        text-align: center;
    }

    #hex-section {
        margin: 1 0 0 0;
        height: auto;
    }

    #hex-section Label {
        margin: 0 0 0 0;
    }

    #hex-input {
        margin: 0 0 0 0;
    }

    #hex-row {
        height: auto;
        align: left middle;
    }

    #hex-preview {
        width: 6;
        height: 3;
        margin: 0 0 0 1;
    }

    #hex-apply {
        margin: 0 0 0 1;
    }
    """

    def __init__(self, title: str, current: str) -> None:
        super().__init__()
        self._title = title
        self._current = current

    def compose(self) -> ComposeResult:
        with Vertical(id="color-dialog"):
            yield Label(self._title, id="color-dialog-title")

            with Horizontal(id="color-palette"):
                for c in _COLOR_NAMES:
                    yield Button(
                        _color_label(c),
                        id=f"pal-{c}",
                        classes="palette-btn",
                    )

            with Vertical(id="hex-section"):
                yield Label(t("wizard.custom_hex"))
                with Horizontal(id="hex-row"):
                    yield Input(
                        placeholder="#FF5500",
                        id="hex-input",
                        max_length=7,
                    )
                    yield Static(" ", id="hex-preview")
                    yield Button(
                        "OK",
                        id="hex-apply",
                        variant="primary",
                    )

    def on_mount(self) -> None:
        """Style palette buttons with their colors."""
        for c in _COLOR_NAMES:
            btn = self.query_one(f"#pal-{c}", Button)
            hex_c = color_hex(c)
            fg = auto_contrast(hex_c)
            btn.styles.background = hex_c
            btn.styles.color = fg

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle palette button or hex apply."""
        btn_id = event.button.id or ""
        if btn_id.startswith("pal-"):
            self.dismiss(btn_id[4:])
        elif btn_id == "hex-apply":
            self._apply_hex()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Update hex preview as user types."""
        if event.input.id == "hex-input":
            val = event.value.strip()
            preview = self.query_one("#hex-preview", Static)
            if _HEX_PATTERN.match(val):
                preview.styles.background = val
            else:
                preview.styles.background = "#808080"

    def _apply_hex(self) -> None:
        """Apply the custom hex value."""
        val = self.query_one("#hex-input", Input).value.strip()
        if _HEX_PATTERN.match(val):
            self.dismiss(val.lower())

    def action_cancel(self) -> None:
        self.dismiss(None)


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------

class NewGameResult:
    """Result of the wizard: human team, all teams by girone, and config info."""

    def __init__(
        self,
        human_team: Team,
        gironi: list[list[Team]],
        province: str,
        region: str,
        comune: str,
        season_year: str,
    ) -> None:
        self.human_team = human_team
        self.gironi = gironi
        self.province = province
        self.region = region
        self.comune = comune
        self.season_year = season_year


# ---------------------------------------------------------------------------
# Main wizard screen
# ---------------------------------------------------------------------------

class NewGameScreen(Screen[NewGameResult | None]):
    """Multi-step wizard for starting a new career."""

    BINDINGS = [
        ("escape", "cancel", t("wizard.back")),
        ("enter", "confirm", t("wizard.next")),
    ]

    CSS = """
    NewGameScreen {
        layout: vertical;
    }

    #step-header {
        text-align: center;
        text-style: bold;
        padding: 1;
        background: $primary;
        width: 100%;
    }

    .wizard-step {
        height: 1fr;
        margin: 1 2;
    }

    /* -- Grid selection (regions, provinces, comuni) -- */

    .box-grid {
        height: 1fr;
        padding: 1;
    }

    .box-grid-inner {
        layout: grid;
        grid-size: 4;
        grid-gutter: 1;
        grid-rows: auto;
        height: auto;
        width: 100%;
    }

    .grid-btn {
        width: 100%;
        height: 5;
        content-align: center middle;
    }

    .search-input {
        margin: 0 0 1 0;
    }

    /* -- Customize form -- */

    #customize-form {
        padding: 1 2;
        height: 1fr;
    }

    #customize-form .form-label {
        margin: 1 0 0 0;
        text-style: bold;
    }

    #customize-form Input {
        margin: 0 0 1 0;
    }

    .color-box {
        width: 100%;
        height: 3;
        content-align: center middle;
        text-align: center;
        text-style: bold;
        margin: 0 0 1 0;
    }

    #color-preview-bar {
        height: 3;
        width: 100%;
        content-align: center middle;
        text-align: center;
        text-style: bold;
        margin: 1 0;
    }

    /* -- Preview -- */

    .preview-container {
        height: 1fr;
    }

    #preview-summary {
        padding: 0 0 1 0;
        color: $text-muted;
    }

    .girone-label {
        text-style: bold;
        padding: 1 0 0 0;
        color: $accent;
    }

    .girone-table {
        height: auto;
        max-height: 14;
        margin: 0 0 1 0;
    }

    .error-label {
        color: $error;
        text-align: center;
        padding: 0 0 1 0;
    }
    """

    step: reactive[int] = reactive(1)

    def __init__(self) -> None:
        super().__init__()
        self._regions: list[str] = []
        self._provinces: list[str] = []
        self._comuni: list[str] = []

        self._selected_region: str = ""
        self._selected_province: str = ""
        self._selected_comune: str = ""

        self._color1: str = "rosso"
        self._color2: str = "bianco"

        self._human_team: Team | None = None
        self._gironi: list[list[Team]] = []
        self._season_year = compute_season_year(default_start_year())

    def compose(self) -> ComposeResult:
        yield Label(t("wizard.step_region"), id="step-header")

        # Step 1: Region selection
        with Vertical(id="step-1", classes="wizard-step"):
            yield VerticalScroll(id="region-grid", classes="box-grid")

        # Step 2: Province selection
        with Vertical(id="step-2", classes="wizard-step"):
            yield VerticalScroll(id="province-grid", classes="box-grid")

        # Step 3: Comune selection
        with Vertical(id="step-3", classes="wizard-step"):
            yield Input(
                placeholder=t("wizard.search_placeholder"),
                id="search-comune",
                classes="search-input",
            )
            yield VerticalScroll(id="comune-grid", classes="box-grid")

        # Step 4: Team customization
        with (
            Vertical(id="step-4", classes="wizard-step"),
            VerticalScroll(id="customize-form"),
        ):
                yield Label(t("wizard.team_name_label"), classes="form-label")
                yield Input(id="input-team-name")

                yield Label(t("wizard.color1_label"), classes="form-label")
                yield Button("", id="color-box-1", classes="color-box")

                yield Label(t("wizard.color2_label"), classes="form-label")
                yield Button("", id="color-box-2", classes="color-box")

                yield Static("", id="color-preview-bar")

                yield Label(t("wizard.stadium_label"), classes="form-label")
                yield Input(id="input-stadium")
                yield Label("", id="customize-error", classes="error-label")

        # Step 5: Tournament preview
        with Vertical(id="step-5", classes="wizard-step"):
            yield Label("", id="preview-summary")
            with VerticalScroll(classes="preview-container"):
                yield Vertical(id="gironi-container")

        yield Footer()

    async def on_mount(self) -> None:
        """Load regions and populate the grid."""
        self._regions = get_regions()
        await self._populate_region_grid()
        self._update_color_boxes()
        self._update_step_visibility()

    # -- Grid population ------------------------------------------------------

    async def _populate_region_grid(self) -> None:
        """Fill the region grid with buttons."""
        grid = self.query_one("#region-grid", VerticalScroll)
        await grid.remove_children()
        self._region_map: dict[str, str] = {}
        buttons: list[Button] = []
        for region in self._regions:
            btn_id = f"reg-{_safe_id(region)}"
            self._region_map[btn_id] = region
            buttons.append(Button(region, id=btn_id, classes="grid-btn"))
        await grid.mount(Horizontal(*buttons, classes="box-grid-inner"))

    async def _populate_province_grid(self) -> None:
        """Fill the province grid with buttons."""
        grid = self.query_one("#province-grid", VerticalScroll)
        await grid.remove_children()
        self._province_map: dict[str, str] = {}
        buttons: list[Button] = []
        for province in self._provinces:
            btn_id = f"prov-{_safe_id(province)}"
            self._province_map[btn_id] = province
            buttons.append(Button(province, id=btn_id, classes="grid-btn"))
        await grid.mount(Horizontal(*buttons, classes="box-grid-inner"))

    async def _populate_comune_grid(
        self, items: list[str] | None = None,
    ) -> None:
        """Fill the comune grid with buttons."""
        grid = self.query_one("#comune-grid", VerticalScroll)
        await grid.remove_children()
        display_items = items if items is not None else self._comuni
        self._comune_map: dict[str, str] = {}
        buttons: list[Button] = []
        for comune in display_items:
            btn_id = f"com-{_safe_id(comune)}"
            self._comune_map[btn_id] = comune
            buttons.append(Button(comune, id=btn_id, classes="grid-btn"))
        await grid.mount(Horizontal(*buttons, classes="box-grid-inner"))

    # -- Color boxes ----------------------------------------------------------

    def _update_color_boxes(self) -> None:
        """Update the two color box buttons and preview bar."""
        for attr, box_id in [
            ("_color1", "color-box-1"),
            ("_color2", "color-box-2"),
        ]:
            color = getattr(self, attr)
            hex_c = _color_to_hex(color)
            fg = auto_contrast(hex_c)
            label = _color_label(color)
            btn = self.query_one(f"#{box_id}", Button)
            btn.label = label
            btn.styles.background = hex_c
            btn.styles.color = fg

        # Preview bar
        hex1 = _color_to_hex(self._color1)
        hex2 = _color_to_hex(self._color2)
        fg1 = auto_contrast(hex1)
        fg2 = auto_contrast(hex2)
        label1 = _color_label(self._color1)
        label2 = _color_label(self._color2)
        preview = self.query_one("#color-preview-bar", Static)
        preview.update(
            f"[{fg1} on {hex1}]  {label1}  [/]"
            f"[{fg2} on {hex2}]  {label2}  [/]"
        )

    def _open_color_picker(self, which: int) -> None:
        """Open the color picker modal for color 1 or 2."""
        if which == 1:
            title = t("wizard.color1_label")
            current = self._color1
        else:
            title = t("wizard.color2_label")
            current = self._color2

        def on_result(result: str | None) -> None:
            if result is None:
                return
            if which == 1:
                self._color1 = result
            else:
                self._color2 = result
            self._update_color_boxes()

        self.app.push_screen(
            ColorPickerModal(title, current),
            callback=on_result,
        )

    # -- Step visibility ------------------------------------------------------

    def watch_step(self, new_step: int) -> None:
        """Update UI when step changes."""
        self._update_step_visibility()

    def _update_step_visibility(self) -> None:
        """Show only the active step container."""
        for i in range(1, 6):
            container = self.query_one(f"#step-{i}")
            container.display = i == self.step

        header = self.query_one("#step-header", Label)
        title_key = _STEP_TITLES.get(self.step, "wizard.title")
        header.update(f"{t(title_key)}  ({self.step}/5)")

    # -- Event handlers -------------------------------------------------------

    async def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes for comuni."""
        if event.input.id == "search-comune":
            query = event.value.strip().lower()
            filtered = [
                c for c in self._comuni if query in c.lower()
            ] if query else self._comuni
            await self._populate_comune_grid(filtered)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle all button presses."""
        btn_id = event.button.id or ""

        if btn_id.startswith("reg-"):
            region = self._region_map.get(btn_id, "")
            if region:
                self._selected_region = region
                self._provinces = get_provinces(region)
                await self._populate_province_grid()
                self.step = 2

        elif btn_id.startswith("prov-"):
            province = self._province_map.get(btn_id, "")
            if province:
                self._selected_province = province
                self._comuni = get_comuni(province)
                self.query_one("#search-comune", Input).value = ""
                await self._populate_comune_grid()
                self.step = 3

        elif btn_id.startswith("com-"):
            comune = getattr(self, "_comune_map", {}).get(btn_id, "")
            if comune:
                self._selected_comune = comune
                self._setup_customize_step()
                self.step = 4

        elif btn_id == "color-box-1":
            self._open_color_picker(1)

        elif btn_id == "color-box-2":
            self._open_color_picker(2)

    # -- Customize step -------------------------------------------------------

    def _setup_customize_step(self) -> None:
        """Pre-fill customization form with defaults."""
        self.query_one("#input-team-name", Input).value = self._selected_comune
        self.query_one("#input-stadium", Input).value = t(
            "wizard.stadium_default", comune=self._selected_comune,
        )
        self._update_color_boxes()

    def _validate_customize(self) -> bool:
        """Validate the customization form."""
        error_label = self.query_one("#customize-error", Label)

        team_name = self.query_one("#input-team-name", Input).value.strip()
        if not team_name:
            error_label.update(t("wizard.name_empty_error"))
            return False

        stadium = self.query_one("#input-stadium", Input).value.strip()
        if not stadium:
            error_label.update(t("wizard.name_empty_error"))
            return False

        if self._color1 == self._color2:
            error_label.update(t("wizard.colors_same_error"))
            return False

        error_label.update("")
        return True

    # -- Tournament generation ------------------------------------------------

    def _generate_tournament(self) -> None:
        """Generate teams and gironi for the tournament preview."""
        all_comuni = get_comuni(self._selected_province)
        num_groups, teams_per_group = calculate_gironi_structure(len(all_comuni))

        opponent_comuni = select_tournament_comuni(
            all_comuni, self._selected_comune, num_groups, teams_per_group,
        )
        opponent_teams = generate_tournament_teams(
            opponent_comuni,
            self._selected_province,
            season=self._season_year,
        )

        team_name = self.query_one("#input-team-name", Input).value.strip()
        stadium = self.query_one("#input-stadium", Input).value.strip()

        self._human_team = generate_team(
            name=team_name,
            city=self._selected_comune,
            province=self._selected_province,
            quality_base=10,
            season=self._season_year,
            is_human=True,
            colors=(self._color1, self._color2),
            stadium_name=stadium,
        )

        all_teams = [self._human_team] + opponent_teams
        self._gironi = generate_gironi(all_teams, num_groups)
        self._render_preview()

    def _render_preview(self) -> None:
        """Render the gironi preview."""
        total_teams = sum(len(g) for g in self._gironi)

        summary = self.query_one("#preview-summary", Label)
        summary.update(
            t("wizard.season_label", year=self._season_year)
            + " — "
            + t("wizard.groups_label", num=len(self._gironi), total=total_teams)
        )

        container = self.query_one("#gironi-container", Vertical)
        container.remove_children()

        # Find the human team's girone
        human_girone_idx = 0
        for idx, girone in enumerate(self._gironi):
            if any(tm.is_human for tm in girone):
                human_girone_idx = idx
                break

        # Render human girone as full table
        human_girone = self._gironi[human_girone_idx]
        idx_h = human_girone_idx
        letter = (
            string.ascii_uppercase[idx_h] if idx_h < 26 else str(idx_h + 1)
        )
        container.mount(Label(
            t("wizard.girone_header", letter=letter)
            + f" {t('wizard.your_team')}",
            classes="girone-label",
        ))

        table: DataTable[str] = DataTable(classes="girone-table")
        table.add_columns(
            t("wizard.col_team"),
            t("wizard.col_city"),
            t("wizard.col_colors"),
            t("wizard.col_average"),
        )
        for team in human_girone:
            marker = f" {t('wizard.your_team')}" if team.is_human else ""
            c1 = _color_label(team.colors[0])
            c2 = _color_label(team.colors[1])
            table.add_row(
                f"{team.name}{marker}",
                team.city,
                f"{c1}/{c2}",
                f"{team.squad_average_overall:.1f}",
            )
        container.mount(table)

        # Other gironi as compact summaries
        if len(self._gironi) > 1:
            container.mount(Label(
                t("wizard.other_gironi"),
                classes="girone-label",
            ))
            for idx, girone in enumerate(self._gironi):
                if idx == human_girone_idx:
                    continue
                gl = (
                    string.ascii_uppercase[idx]
                    if idx < 26 else str(idx + 1)
                )
                names = ", ".join(tm.name for tm in girone)
                container.mount(Label(
                    f"[bold]{t('wizard.girone_header', letter=gl)}[/bold]"
                    f" ({len(girone)}) — {names}",
                ))

    # -- Navigation -----------------------------------------------------------

    def action_confirm(self) -> None:
        """Handle Enter key: advance any wizard step."""
        if self.step == 1:
            self._press_grid_button("#region-grid")
        elif self.step == 2:
            self._press_grid_button("#province-grid")
        elif self.step == 3:
            self._press_grid_button("#comune-grid")
        elif self.step == 4:
            if self._validate_customize():
                self._generate_tournament()
                self.step = 5
        elif self.step == 5:
            self._finish()

    def _press_grid_button(self, grid_id: str) -> None:
        """Press the focused grid button, or the first one if nothing is focused."""
        focused = self.focused
        if isinstance(focused, Button):
            grid = self.query_one(grid_id)
            if focused in grid.query(Button):
                focused.press()
                return
        buttons = self.query_one(grid_id).query(Button)
        if buttons:
            buttons.first(Button).press()

    def _finish(self) -> None:
        """Complete the wizard and dismiss with result."""
        if self._human_team is None:
            return

        region = (
            get_region_for_province(self._selected_province)
            or self._selected_region
        )
        self.dismiss(NewGameResult(
            human_team=self._human_team,
            gironi=self._gironi,
            province=self._selected_province,
            region=region,
            comune=self._selected_comune,
            season_year=self._season_year,
        ))

    def action_cancel(self) -> None:
        """Handle escape: go back or cancel."""
        if self.step > 1:
            self.step -= 1
        else:
            self.dismiss(None)
