"""Modal dialog for changing team tactic during a match."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static

from calcio_manager.i18n import t
from calcio_manager.models.enums import TacticStyle


class TacticModal(ModalScreen[TacticStyle | None]):
    """Quick tactic selector — returns the chosen TacticStyle or None."""

    BINDINGS = [("escape", "cancel", "")]

    CSS = """
    TacticModal {
        align: center middle;
        background: $background 60%;
    }

    #tactic-dialog {
        width: 40;
        height: auto;
        padding: 1 2;
        background: $boost;
        border: heavy $primary;
    }

    #tactic-title {
        text-align: center;
        text-style: bold;
        width: 100%;
        padding: 0 0 1 0;
    }

    #tactic-current {
        text-align: center;
        color: $text-muted;
        width: 100%;
        padding: 0 0 1 0;
    }

    .tactic-btn {
        width: 100%;
        margin: 0 0 1 0;
    }

    .tactic-btn.active {
        border: wide $success;
    }
    """

    def __init__(self, current: TacticStyle) -> None:
        super().__init__()
        self._current = current

    def compose(self) -> ComposeResult:
        with Vertical(id="tactic-dialog"):
            yield Static(t("match.tactic_dialog.title"), id="tactic-title")
            current_label = t(f"tactics.{self._current.value}")
            yield Static(
                t("match.tactic_dialog.current", tactic=current_label),
                id="tactic-current",
            )
            for style in TacticStyle:
                label = t(f"tactics.{style.value}")
                btn = Button(
                    label,
                    id=f"tactic-{style.value}",
                    classes="tactic-btn",
                    variant="success" if style == self._current else "default",
                )
                yield btn

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Return the selected tactic."""
        btn_id = event.button.id or ""
        prefix = "tactic-"
        if btn_id.startswith(prefix):
            value = btn_id[len(prefix):]
            for style in TacticStyle:
                if style.value == value:
                    self.dismiss(style)
                    return

    def action_cancel(self) -> None:
        """Dismiss without changing."""
        self.dismiss(None)
