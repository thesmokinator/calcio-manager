"""Load game dialog screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Center, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, DataTable, Static

from calcio_manager.i18n import t
from calcio_manager.state.save_load import delete_save, list_saves


class LoadGameScreen(Screen[str | None]):
    """Dialog for selecting a saved game to load."""

    BINDINGS = [
        ("escape", "cancel", t("load_game.cancel")),
    ]

    CSS = """
    LoadGameScreen {
        align: center middle;
    }

    #load-dialog {
        width: 90;
        height: auto;
        max-height: 32;
        padding: 2 4;
        background: $boost;
        border: heavy $primary;
    }

    #load-title {
        text-align: center;
        text-style: bold;
        width: 100%;
        padding: 0 0 1 0;
    }

    #no-saves {
        text-align: center;
        color: $text-muted;
        padding: 2 0;
    }

    #saves-table {
        height: auto;
        max-height: 16;
        margin: 0 0 1 0;
    }

    .load-buttons {
        height: auto;
        align: center middle;
        padding: 1 0 0 0;
    }

    .load-buttons Button {
        width: 20;
        margin: 0 2;
    }

    #confirm-bar {
        height: auto;
        align: center middle;
        padding: 1 0 0 0;
        display: none;
    }

    #confirm-label {
        text-align: center;
        width: 100%;
        color: $error;
        text-style: bold;
        padding: 0 0 1 0;
    }

    #confirm-bar Button {
        width: 20;
        margin: 0 2;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._saves: list[dict[str, str]] = []
        self._confirming_delete: bool = False

    def compose(self) -> ComposeResult:
        with Center(), Vertical(id="load-dialog"):
            yield Static(t("load_game.title"), id="load-title")
            yield DataTable(id="saves-table")
            yield Static(t("load_game.no_saves"), id="no-saves")
            with Horizontal(classes="load-buttons"):
                yield Button(t("load_game.load"), id="load-btn", variant="primary")
                yield Button(t("load_game.delete"), id="delete-btn", variant="error")
                yield Button(t("load_game.cancel"), id="cancel-btn")
            with Vertical(id="confirm-bar"):
                yield Static("", id="confirm-label")
                with Horizontal(classes="load-buttons"):
                    yield Button(t("load_game.confirm"), id="confirm-yes", variant="error")
                    yield Button(t("load_game.no"), id="confirm-no")

    def on_mount(self) -> None:
        """Populate the saves table."""
        self._refresh_saves()

    def _refresh_saves(self) -> None:
        """Reload saves list and repopulate the table."""
        self._saves = list_saves()
        table = self.query_one("#saves-table", DataTable)
        no_saves = self.query_one("#no-saves", Static)

        table.clear(columns=True)

        if not self._saves:
            table.display = False
            self.query_one("#load-btn").display = False
            self.query_one("#delete-btn").display = False
            no_saves.display = True
            return

        no_saves.display = False
        table.display = True
        self.query_one("#load-btn").display = True
        self.query_one("#delete-btn").display = True

        table.cursor_type = "row"
        table.add_columns(
            t("load_game.col_name"),
            t("load_game.col_team"),
            t("load_game.col_province"),
            t("load_game.col_season"),
            t("load_game.col_modified"),
        )

        for save in self._saves:
            table.add_row(
                save["slot"],
                save["team"],
                save["province"],
                save["season"],
                save["modified"],
            )

    def check_action(
        self, action: str, parameters: tuple[object, ...],
    ) -> bool | None:
        """Hide command palette and ESC from footer."""
        if action == "command_palette":
            return None
        if action == "cancel":
            return None
        return True

    def action_cancel(self) -> None:
        """Cancel and return to previous screen."""
        if self._confirming_delete:
            self._hide_confirm()
        else:
            self.dismiss(None)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        if event.button.id == "load-btn":
            self._do_load()
        elif event.button.id == "delete-btn":
            self._show_confirm()
        elif event.button.id == "cancel-btn":
            self.dismiss(None)
        elif event.button.id == "confirm-yes":
            self._do_delete()
        elif event.button.id == "confirm-no":
            self._hide_confirm()

    def _do_load(self) -> None:
        """Dismiss with the selected save slot."""
        if not self._saves:
            return
        table = self.query_one("#saves-table", DataTable)
        if table.cursor_row is not None and 0 <= table.cursor_row < len(self._saves):
            slot = self._saves[table.cursor_row]["slot"]
            self.dismiss(slot)

    def _show_confirm(self) -> None:
        """Show deletion confirmation bar."""
        if not self._saves:
            return
        table = self.query_one("#saves-table", DataTable)
        if table.cursor_row is None or table.cursor_row >= len(self._saves):
            return

        slot = self._saves[table.cursor_row]["slot"]
        self._confirming_delete = True
        self.query_one("#confirm-label", Static).update(
            t("load_game.delete_confirm", slot=slot)
        )
        self.query_one("#confirm-bar").display = True
        self.query_one(".load-buttons").display = False

    def _hide_confirm(self) -> None:
        """Hide deletion confirmation bar."""
        self._confirming_delete = False
        self.query_one("#confirm-bar").display = False
        self.query_one(".load-buttons").display = True

    def _do_delete(self) -> None:
        """Delete the selected save and refresh the list."""
        if not self._saves:
            return
        table = self.query_one("#saves-table", DataTable)
        if table.cursor_row is None or table.cursor_row >= len(self._saves):
            self._hide_confirm()
            return

        slot = self._saves[table.cursor_row]["slot"]
        delete_save(slot)
        self._hide_confirm()
        self._refresh_saves()
