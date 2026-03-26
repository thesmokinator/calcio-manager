"""Main menu screen — full-screen player background with floating menu box."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Static

from calcio_manager.data.player_art import COLS as _ART_COLS
from calcio_manager.data.player_art import DATA as _ART_DATA
from calcio_manager.data.player_art import ROWS as _ART_ROWS
from calcio_manager.i18n import t
from calcio_manager.ui.block_font import render_block
from calcio_manager.ui.widgets.image_background import ImageBackground

_TITLE_LINE1 = render_block("CALCIO")
_TITLE_LINE2 = render_block("MANAGER")


class MainMenuScreen(Screen[str]):
    """The game's main menu — full-screen photo behind a floating box."""

    CSS = """
    MainMenuScreen {
        layers: bg fg;
        align: center middle;
        overflow: hidden;
    }

    ImageBackground {
        layer: bg;
    }

    #menu-box {
        layer: fg;
        width: 62;
        height: auto;
        background: $boost;
        padding: 2 4;
    }

    #title-block {
        text-align: center;
        width: 100%;
        color: $text;
        text-style: bold;
    }

    #game-subtitle {
        text-align: center;
        color: $text-muted;
        text-style: bold;
        width: 100%;
        padding: 1 0 2 0;
    }

    .menu-row {
        height: auto;
        align: center middle;
    }

    .menu-box-btn {
        width: 24;
        height: 5;
        margin: 1 1;
        content-align: center middle;
    }

    #quit {
        width: 24;
        height: 5;
        margin: 1 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield ImageBackground(_ART_DATA, _ART_COLS, _ART_ROWS, x_pan_pct=0.2)
        with Vertical(id="menu-box"):
            yield Static(
                f"{_TITLE_LINE1}\n\n{_TITLE_LINE2}",
                id="title-block",
            )
            yield Static(
                t("app.subtitle"),
                id="game-subtitle",
            )
            with Horizontal(classes="menu-row"):
                yield Button(
                    t("menu.new_game"), id="new-game",
                    variant="primary", classes="menu-box-btn",
                )
                yield Button(
                    t("menu.load_game"), id="load-game",
                    classes="menu-box-btn",
                )
            with Horizontal(classes="menu-row"):
                yield Button(
                    t("menu.settings"), id="settings",
                    classes="menu-box-btn",
                )
                yield Button(
                    t("menu.credits"), id="credits",
                    classes="menu-box-btn",
                )
            with Horizontal(classes="menu-row"):
                yield Button(
                    t("menu.quit"), id="quit",
                    variant="error",
                )

    def check_action(
        self, action: str, parameters: tuple[object, ...],
    ) -> bool | None:
        """Hide command palette."""
        if action == "command_palette":
            return None
        return True

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle menu button clicks."""
        if event.button.id == "new-game":
            self.dismiss("new-game")
        elif event.button.id == "load-game":
            self.dismiss("load-game")
        elif event.button.id == "settings":
            self.dismiss("settings")
        elif event.button.id == "credits":
            self.dismiss("credits")
        elif event.button.id == "quit":
            self.app.exit()
