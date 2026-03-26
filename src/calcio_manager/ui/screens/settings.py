"""Settings screen — language selection."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Center, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Label, Select, Static

from calcio_manager.i18n import current_locale, t
from calcio_manager.state.settings import (
    SUPPORTED_LANGUAGES,
    AppSettings,
    load_settings,
    save_settings,
)


class SettingsScreen(Screen[None]):
    """Application settings dialog."""

    BINDINGS = [
        ("escape", "cancel", t("settings.back")),
    ]

    CSS = """
    SettingsScreen {
        align: center middle;
    }

    #settings-dialog {
        width: 60;
        height: auto;
        padding: 2 4;
        background: $boost;
        border: heavy $primary;
    }

    #settings-title {
        text-align: center;
        text-style: bold;
        width: 100%;
        padding: 0 0 2 0;
    }

    .settings-field {
        height: auto;
        margin: 0 0 1 0;
    }

    .settings-label {
        padding: 0 0 1 0;
    }

    .settings-buttons {
        height: auto;
        align: center middle;
        padding: 1 0 0 0;
    }

    .settings-buttons Button {
        width: 20;
        margin: 0 2;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._current_settings = load_settings()

    def compose(self) -> ComposeResult:
        options = [
            (label, code) for code, label in SUPPORTED_LANGUAGES.items()
        ]
        with Center(), Vertical(id="settings-dialog"):
            yield Static(t("settings.title"), id="settings-title")
            with Vertical(classes="settings-field"):
                yield Label(t("settings.language"), classes="settings-label")
                yield Select(
                    options,
                    value=self._current_settings.language,
                    id="lang-select",
                    allow_blank=False,
                )
            with Horizontal(classes="settings-buttons"):
                yield Button(
                    t("settings.save"), id="save-btn", variant="primary",
                )
                yield Button(t("settings.cancel"), id="cancel-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle save/cancel."""
        if event.button.id == "save-btn":
            self._do_save()
        elif event.button.id == "cancel-btn":
            self.dismiss(None)

    def action_cancel(self) -> None:
        """Cancel and return."""
        self.dismiss(None)

    def _do_save(self) -> None:
        """Persist settings and dismiss."""
        select = self.query_one("#lang-select", Select)
        lang = str(select.value) if select.value is not Select.BLANK else current_locale()
        save_settings(AppSettings(language=lang))
        self.notify(t("settings.saved"))
        self.dismiss(None)
