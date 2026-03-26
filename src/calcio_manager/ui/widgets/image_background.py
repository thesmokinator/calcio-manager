"""Reusable full-screen image background widget using half-block characters."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.segment import Segment
from rich.style import Style
from textual.widget import Widget

if TYPE_CHECKING:
    from rich.console import Console, ConsoleOptions, RenderResult


def precompute_styles(hex_data: str, cols: int, rows: int) -> list[list[Style]]:
    """Decode hex art data into a grid of Rich styles for half-block rendering."""
    raw = bytes.fromhex(hex_data)
    styles: list[list[Style]] = []
    for row in range(rows):
        row_styles: list[Style] = []
        for col in range(cols):
            off = (row * cols + col) * 6
            r1, g1, b1 = raw[off], raw[off + 1], raw[off + 2]
            r2, g2, b2 = raw[off + 3], raw[off + 4], raw[off + 5]
            row_styles.append(
                Style(
                    color=f"#{r1:02x}{g1:02x}{b1:02x}",
                    bgcolor=f"#{r2:02x}{g2:02x}{b2:02x}",
                ),
            )
        styles.append(row_styles)
    return styles


class _ImageRenderable:
    """Rich renderable — scales pre-rendered half-block art to fill any size."""

    def __init__(
        self,
        width: int,
        height: int,
        styles: list[list[Style]],
        art_cols: int,
        art_rows: int,
        x_pan_pct: float = 0.0,
    ) -> None:
        self.width = width
        self.height = height
        self.styles = styles
        self.art_cols = art_cols
        self.art_rows = art_rows
        self.x_pan_pct = x_pan_pct

    def __rich_console__(
        self, console: Console, options: ConsoleOptions,
    ) -> RenderResult:
        w, h = self.width, self.height
        if w < 2 or h < 2:
            return

        x_pan = int(self.art_cols * self.x_pan_pct)
        x_range = self.art_cols - x_pan

        for sy in range(h):
            ay = min(sy * self.art_rows // h, self.art_rows - 1)
            row_styles = self.styles[ay]
            for sx in range(w):
                ax = min(x_pan + sx * x_range // w, self.art_cols - 1)
                yield Segment("\u2580", row_styles[ax])
            if sy < h - 1:
                yield Segment("\n")


class ImageBackground(Widget):
    """Full-screen widget that renders a pre-computed image as a muted background.

    Args:
        hex_data: Hex-encoded art data (6 bytes per cell: R1G1B1 R2G2B2).
        art_cols: Number of columns in the art data.
        art_rows: Number of rows in the art data.
        x_pan_pct: Fraction of the image to skip from the left (0.0-1.0).
    """

    can_focus = False

    DEFAULT_CSS = """
    ImageBackground {
        width: 100%;
        height: 100%;
    }
    """

    def __init__(
        self,
        hex_data: str,
        art_cols: int,
        art_rows: int,
        x_pan_pct: float = 0.0,
        **kwargs: str,
    ) -> None:
        super().__init__(**kwargs)  # type: ignore[arg-type]
        self._styles = precompute_styles(hex_data, art_cols, art_rows)
        self._art_cols = art_cols
        self._art_rows = art_rows
        self._x_pan_pct = x_pan_pct

    def render(self) -> _ImageRenderable:
        """Render the image background scaled to the current widget size."""
        return _ImageRenderable(
            self.size.width,
            self.size.height,
            self._styles,
            self._art_cols,
            self._art_rows,
            self._x_pan_pct,
        )
