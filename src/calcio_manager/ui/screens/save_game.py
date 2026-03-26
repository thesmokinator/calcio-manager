"""Save game dialog screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Center, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Static

from calcio_manager.i18n import t


class SaveGameScreen(Screen[str | None]):
    """Dialog for saving the game with a custom name."""

    BINDINGS = [
        ("escape", "cancel", t("save_game.cancel")),
    ]

    CSS = """
    SaveGameScreen {
        align: center middle;
    }

    #save-dialog {
        width: 60;
        height: auto;
        padding: 2 4;
        background: $boost;
        border: heavy $primary;
    }

    #save-title {
        text-align: center;
        text-style: bold;
        width: 100%;
        padding: 0 0 1 0;
    }

    #save-label {
        padding: 0 0 1 0;
    }

    #save-input {
        margin: 0 0 1 0;
    }

    .save-buttons {
        height: auto;
        align: center middle;
        padding: 1 0 0 0;
    }

    .save-buttons Button {
        width: 20;
        margin: 0 2;
    }
    """

    def __init__(self, default_name: str = "") -> None:
        super().__init__()
        self._default_name = default_name or "Save"

    def compose(self) -> ComposeResult:
        with Center(), Vertical(id="save-dialog"):
            yield Static(t("save_game.title"), id="save-title")
            yield Label(t("save_game.label"), id="save-label")
            yield Input(
                value=self._default_name,
                placeholder=t("save_game.placeholder"),
                id="save-input",
            )
            with Horizontal(classes="save-buttons"):
                yield Button(t("save_game.save"), id="save-btn", variant="primary")
                yield Button(t("save_game.cancel"), id="cancel-btn")

    def on_mount(self) -> None:
        """Focus the input field."""
        self.query_one("#save-input", Input).focus()

    def on_input_submitted(self) -> None:
        """Handle Enter in the input field."""
        self._do_save()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        if event.button.id == "save-btn":
            self._do_save()
        elif event.button.id == "cancel-btn":
            self.dismiss(None)

    def action_cancel(self) -> None:
        """Cancel and return to previous screen."""
        self.dismiss(None)

    def _do_save(self) -> None:
        """Validate and dismiss with the save name."""
        name = self.query_one("#save-input", Input).value.strip()
        if not name:
            self.notify(t("save_game.empty_error"), title=t("save_game.error"))
            return
        slot = "".join(
            c if c.isalnum() or c in "-_" else "_" for c in name
        )
        self.dismiss(slot)
