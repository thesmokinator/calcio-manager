"""Credits screen — shows project info, license, author, and repository."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Center, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Label, Static

from calcio_manager.i18n import t

_VERSION = "0.1.0"
_AUTHOR = "Michele Broggi"
_LICENSE = "MIT"
_REPOSITORY = "github.com/thesmokinator/calcio-manager"


class CreditsScreen(Screen[None]):
    """Application credits dialog."""

    BINDINGS = [
        ("escape", "close", t("credits.back")),
    ]

    CSS = """
    CreditsScreen {
        align: center middle;
    }

    #credits-dialog {
        width: 60;
        height: auto;
        padding: 2 4;
        background: $boost;
        border: heavy $primary;
    }

    #credits-title {
        text-align: center;
        text-style: bold;
        width: 100%;
        padding: 0 0 2 0;
    }

    .credits-row {
        height: auto;
        margin: 0 0 1 0;
    }

    .credits-label {
        width: 16;
        text-style: bold;
        color: #eab308;
    }

    .credits-value {
        width: 1fr;
    }

    .credits-buttons {
        height: auto;
        align: center middle;
        padding: 1 0 0 0;
    }

    .credits-buttons Button {
        width: 20;
    }
    """

    def compose(self) -> ComposeResult:
        with Center(), Vertical(id="credits-dialog"):
            yield Static(t("credits.title"), id="credits-title")
            with Horizontal(classes="credits-row"):
                yield Label(t("credits.version"), classes="credits-label")
                yield Label(_VERSION, classes="credits-value")
            with Horizontal(classes="credits-row"):
                yield Label(t("credits.author"), classes="credits-label")
                yield Label(_AUTHOR, classes="credits-value")
            with Horizontal(classes="credits-row"):
                yield Label(t("credits.license"), classes="credits-label")
                yield Label(_LICENSE, classes="credits-value")
            with Horizontal(classes="credits-row"):
                yield Label(t("credits.repository"), classes="credits-label")
                yield Label(_REPOSITORY, classes="credits-value")
            with Horizontal(classes="credits-buttons"):
                yield Button(t("credits.close"), id="close-btn", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle close."""
        if event.button.id == "close-btn":
            self.dismiss(None)

    def action_close(self) -> None:
        """Close and return."""
        self.dismiss(None)
