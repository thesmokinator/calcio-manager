"""Application-level settings persisted at ~/.calcio_manager/settings.toml."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

SETTINGS_DIR = Path.home() / ".calcio_manager"
SETTINGS_PATH = SETTINGS_DIR / "settings.toml"

SUPPORTED_LANGUAGES = {"it": "Italiano", "en": "English"}
DEFAULT_LANGUAGE = "it"


@dataclass
class AppSettings:
    """Application settings (not per-save)."""

    language: str = DEFAULT_LANGUAGE


def load_settings() -> AppSettings:
    """Load settings from disk, returning defaults if the file is missing."""
    if not SETTINGS_PATH.exists():
        return AppSettings()
    try:
        with open(SETTINGS_PATH, "rb") as f:
            data = tomllib.load(f)
        lang = data.get("language", DEFAULT_LANGUAGE)
        if lang not in SUPPORTED_LANGUAGES:
            lang = DEFAULT_LANGUAGE
        return AppSettings(language=lang)
    except (tomllib.TOMLDecodeError, OSError):
        return AppSettings()


def save_settings(settings: AppSettings) -> None:
    """Write settings to disk as a TOML file."""
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    lines = [f'language = "{settings.language}"\n']
    SETTINGS_PATH.write_text("".join(lines), encoding="utf-8")
