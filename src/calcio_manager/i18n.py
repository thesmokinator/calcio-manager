"""Internationalization module — TOML-based translations.

Auto-initializes on import by reading ``~/.calcio_manager/settings.toml``.
All UI code can simply ``from calcio_manager.i18n import t, format_date``.
"""

from __future__ import annotations

import tomllib
from datetime import date
from pathlib import Path

_LOCALE_DIR = Path(__file__).parent / "data" / "locale"
_strings: dict[str, object] = {}
_current_locale: str = "it"


# -- internal helpers --------------------------------------------------------


def _load_locale(lang: str) -> None:
    """Read a locale TOML file into *_strings*."""
    global _strings
    path = _LOCALE_DIR / f"{lang}.toml"
    if not path.exists():
        path = _LOCALE_DIR / "it.toml"
    with open(path, "rb") as f:
        _strings = tomllib.load(f)


def _resolve(key: str) -> object:
    """Walk dotted *key* through the nested dict."""
    obj: object = _strings
    for part in key.split("."):
        if isinstance(obj, dict):
            obj = obj.get(part)
        else:
            return None
        if obj is None:
            return None
    return obj


# -- public API --------------------------------------------------------------


def t(key: str, **kwargs: object) -> str:
    """Translate *key*, optionally interpolating *kwargs*.

    Returns *key* itself when the translation is missing so that untranslated
    strings are visible but the app doesn't crash.
    """
    val = _resolve(key)
    if not isinstance(val, str):
        return key
    if kwargs:
        try:
            return val.format(**kwargs)
        except (KeyError, IndexError):
            return val
    return val


def t_list(key: str) -> list[str]:
    """Return a TOML array of strings by dotted *key*."""
    val = _resolve(key)
    if isinstance(val, list):
        return [str(x) for x in val]
    return []


def format_date(d: date) -> str:
    """Format *d* using the current locale's day/month names."""
    days = t_list("dates.days")
    months = t_list("dates.months")
    if not days or not months:
        return str(d)
    day_name = days[d.weekday()] if d.weekday() < len(days) else ""
    month_name = months[d.month] if d.month < len(months) else ""
    return f"{day_name} {d.day} {month_name} {d.year}"


def current_locale() -> str:
    """Return the active locale code (e.g. ``'it'``, ``'en'``)."""
    return _current_locale


def set_locale(lang: str) -> None:
    """Switch locale at runtime (requires app restart for full effect)."""
    global _current_locale
    _current_locale = lang
    _load_locale(lang)


# -- auto-init on first import ----------------------------------------------

def _auto_init() -> None:
    global _current_locale
    # Inline import avoids a circular-import issue if settings ever grows.
    from calcio_manager.state.settings import load_settings
    settings = load_settings()
    _current_locale = settings.language
    _load_locale(settings.language)


_auto_init()
