"""Loader for Italian comuni (municipalities) data."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).parent


@lru_cache(maxsize=1)
def _load_comuni_db() -> dict[str, dict[str, list[str]]]:
    """Load the full comuni database from JSON (cached after first call)."""
    comuni_file = DATA_DIR / "comuni_it.json"
    with open(comuni_file, encoding="utf-8") as f:
        data: dict[str, dict[str, list[str]]] = json.load(f)
    return data


def get_regions() -> list[str]:
    """Return all Italian regions, sorted alphabetically."""
    return sorted(_load_comuni_db().keys())


def get_provinces(region: str) -> list[str]:
    """Return all provinces for a given region, sorted alphabetically."""
    db = _load_comuni_db()
    provinces = db.get(region, {})
    return sorted(provinces.keys())


def get_comuni(province: str) -> list[str]:
    """Return all comuni for a given province, sorted alphabetically.

    Searches across all regions to find the province.
    """
    db = _load_comuni_db()
    for provinces in db.values():
        if province in provinces:
            return sorted(provinces[province])
    return []


def get_region_for_province(province: str) -> str | None:
    """Return the region that contains the given province."""
    db = _load_comuni_db()
    for region, provinces in db.items():
        if province in provinces:
            return region
    return None
