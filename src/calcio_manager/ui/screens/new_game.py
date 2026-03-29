"""New game wizard — multi-step career setup."""

from __future__ import annotations

import string
import unicodedata

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.screen import Screen
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

def _safe_id(text: str) -> str:
    """Convert any text to a valid Textual CSS identifier.

    Strips accents, replaces non-alphanumeric chars with underscores.
    """
    # Normalize unicode: è→e, ù→u, etc.
    nfkd = unicodedata.normalize("NFKD", text)
    ascii_text = nfkd.encode("ascii", "ignore").decode("ascii")
    # Replace non-alnum with underscore
    return "".join(c if c.isalnum() else "_" for c in ascii_text)


_STEP_TITLES = {
    1: "wizard.step_region",
    2: "wizard.step_province",
    3: "wizard.step_comune",
    4: "wizard.step_customize",
    5: "wizard.step_preview",
}


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

    /* -- Grid selection (regions & provinces) -- */

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

    .color-grid {
        layout: grid;
        grid-size: 5;
        grid-gutter: 1;
        grid-rows: auto;
        height: auto;
        width: 100%;
    }

    .color-btn {
        width: 100%;
        height: 3;
        content-align: center middle;
        text-align: center;
        min-width: 12;
    }

    .color-btn.selected {
        border: heavy white;
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
        yield Label(
            t("wizard.step_region"),
            id="step-header",
        )

        # Step 1: Region selection — grid of boxes
        with Vertical(id="step-1", classes="wizard-step"):
            yield VerticalScroll(id="region-grid", classes="box-grid")

        # Step 2: Province selection — grid of boxes
        with Vertical(id="step-2", classes="wizard-step"):
            yield VerticalScroll(id="province-grid", classes="box-grid")

        # Step 3: Comune selection — search + grid of boxes
        with Vertical(id="step-3", classes="wizard-step"):
            yield Input(
                placeholder=t("wizard.search_placeholder"),
                id="search-comune",
                classes="search-input",
            )
            yield VerticalScroll(id="comune-grid", classes="box-grid")

        # Step 4: Team customization
        with Vertical(id="step-4", classes="wizard-step"), VerticalScroll(id="customize-form"):
            yield Label(t("wizard.team_name_label"), classes="form-label")
            yield Input(id="input-team-name")

            yield Label(t("wizard.color1_label"), classes="form-label")
            with Horizontal(id="color-grid-1", classes="color-grid"):
                for c in _COLOR_NAMES:
                    yield Button(
                        t(f"colors.{c}"),
                        classes="color-btn",
                        id=f"c1-{c}",
                    )

            yield Label(t("wizard.color2_label"), classes="form-label")
            with Horizontal(id="color-grid-2", classes="color-grid"):
                for c in _COLOR_NAMES:
                    yield Button(
                        t(f"colors.{c}"),
                        classes="color-btn",
                        id=f"c2-{c}",
                    )

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
        self._apply_color_swatches()
        self._update_color_selection_ui()
        self._update_step_visibility()

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
        container = Horizontal(*buttons, classes="box-grid-inner")
        await grid.mount(container)

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
        container = Horizontal(*buttons, classes="box-grid-inner")
        await grid.mount(container)

    def _apply_color_swatches(self) -> None:
        """Set background and text colors on all color swatch buttons."""
        for prefix in ("c1", "c2"):
            for c in _COLOR_NAMES:
                btn = self.query_one(f"#{prefix}-{c}", Button)
                hex_c = color_hex(c)
                fg = auto_contrast(hex_c)
                btn.styles.background = hex_c
                btn.styles.color = fg

    def watch_step(self, new_step: int) -> None:
        """Update UI when step changes."""
        self._update_step_visibility()

    def _update_step_visibility(self) -> None:
        """Show only the active step container."""
        for i in range(1, 6):
            container = self.query_one(f"#step-{i}")
            container.display = i == self.step

        # Update header bar with step title
        header = self.query_one("#step-header", Label)
        title_key = _STEP_TITLES.get(self.step, "wizard.title")
        step_text = t(title_key)
        header.update(f"{step_text}  ({self.step}/5)")

    async def _populate_comune_grid(self, items: list[str] | None = None) -> None:
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
        container = Horizontal(*buttons, classes="box-grid-inner")
        await grid.mount(container)

    # -- Color selection ------------------------------------------------------

    def _update_color_selection_ui(self) -> None:
        """Update color swatch borders and preview bar."""
        for prefix, selected in [("c1", self._color1), ("c2", self._color2)]:
            for c in _COLOR_NAMES:
                btn = self.query_one(f"#{prefix}-{c}", Button)
                if c == selected:
                    btn.add_class("selected")
                else:
                    btn.remove_class("selected")

        # Update preview bar with auto-contrast text
        hex1 = color_hex(self._color1)
        hex2 = color_hex(self._color2)
        fg1 = auto_contrast(hex1)
        fg2 = auto_contrast(hex2)
        label1 = t(f"colors.{self._color1}")
        label2 = t(f"colors.{self._color2}")
        preview = self.query_one("#color-preview-bar", Static)
        preview.update(
            f"[{fg1} on {hex1}]  {label1}  [/]"
            f"[{fg2} on {hex2}]  {label2}  [/]"
        )

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
        """Handle all button presses: grid selection + actions."""
        btn_id = event.button.id or ""

        # Region grid button
        if btn_id.startswith("reg-"):
            region = self._region_map.get(btn_id, "")
            if region:
                self._selected_region = region
                self._provinces = get_provinces(region)
                await self._populate_province_grid()
                self.step = 2

        # Province grid button
        elif btn_id.startswith("prov-"):
            province = self._province_map.get(btn_id, "")
            if province:
                self._selected_province = province
                self._comuni = get_comuni(province)
                self.query_one("#search-comune", Input).value = ""
                await self._populate_comune_grid()
                self.step = 3

        # Comune grid button
        elif btn_id.startswith("com-"):
            comune = getattr(self, "_comune_map", {}).get(btn_id, "")
            if comune:
                self._selected_comune = comune
                self._setup_customize_step()
                self.step = 4

        # Color picker buttons
        elif btn_id.startswith("c1-"):
            self._color1 = btn_id[3:]
            self._update_color_selection_ui()
        elif btn_id.startswith("c2-"):
            self._color2 = btn_id[3:]
            self._update_color_selection_ui()


    def _setup_customize_step(self) -> None:
        """Pre-fill customization form with defaults."""
        self.query_one("#input-team-name", Input).value = self._selected_comune
        self.query_one("#input-stadium", Input).value = (
            f"Campo Sportivo {self._selected_comune}"
        )

    def _validate_customize(self) -> bool:
        """Validate the customization form. Returns True if valid."""
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
        """Render the gironi preview.

        Shows the human team's girone as a full table,
        other gironi as compact one-line summaries.
        """
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
        letter = string.ascii_uppercase[idx_h] if idx_h < 26 else str(idx_h + 1)
        container.mount(Label(
            t("wizard.girone_header", letter=letter) + f" {t('wizard.your_team')}",
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
            c1_label = t(f"colors.{team.colors[0]}")
            c2_label = t(f"colors.{team.colors[1]}")
            table.add_row(
                f"{team.name}{marker}",
                team.city,
                f"{c1_label}/{c2_label}",
                f"{team.squad_average_overall:.1f}",
            )
        container.mount(table)

        # Render other gironi as compact summary
        if len(self._gironi) > 1:
            container.mount(Label(
                t("wizard.other_gironi"),
                classes="girone-label",
            ))
            for idx, girone in enumerate(self._gironi):
                if idx == human_girone_idx:
                    continue
                letter = string.ascii_uppercase[idx] if idx < 26 else str(idx + 1)
                team_names = ", ".join(tm.name for tm in girone)
                container.mount(Label(
                    f"[bold]{t('wizard.girone_header', letter=letter)}[/bold]"
                    f" ({len(girone)}) — {team_names}",
                ))


    # -- Navigation -----------------------------------------------------------

    def action_confirm(self) -> None:
        """Handle Enter key: advance from customize or start career."""
        if self.step == 4:
            if self._validate_customize():
                self._generate_tournament()
                self.step = 5
        elif self.step == 5:
            self._finish()

    def _finish(self) -> None:
        """Complete the wizard and dismiss with result."""
        if self._human_team is None:
            return

        region = get_region_for_province(self._selected_province) or self._selected_region

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
