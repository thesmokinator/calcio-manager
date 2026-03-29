"""Shared colour utilities for the TUI."""

from __future__ import annotations

# Italian colour names -> hex (tuned for dark-background terminals)
ITALIAN_TO_HEX: dict[str, str] = {
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
    "granata": "#800020",
    "celeste": "#87ceeb",
    "oro": "#ffd700",
    "argento": "#c0c0c0",
    "amaranto": "#9f1d35",
}


def color_hex(name: str) -> str:
    """Convert an Italian colour name to a hex code."""
    return ITALIAN_TO_HEX.get(name, "#808080")


def auto_contrast(bg_hex: str) -> str:
    """Return white or black hex for readable text on *bg_hex*."""
    bg = bg_hex.lstrip("#")
    r, g, b = int(bg[0:2], 16), int(bg[2:4], 16), int(bg[4:6], 16)
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return "#ffffff" if luminance < 0.5 else "#1a1a1a"
