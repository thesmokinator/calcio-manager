"""Save and load game state to/from JSON files."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from calcio_manager.state.game_state import GameState

SAVE_DIR = Path.home() / ".calcio_manager" / "saves"


def _ensure_save_dir() -> None:
    """Create save directory if it doesn't exist."""
    SAVE_DIR.mkdir(parents=True, exist_ok=True)


def save_game(state: GameState, slot: str = "save1") -> Path:
    """Save game state to a JSON file.

    Args:
        state: Complete game state to save.
        slot: Save slot name.

    Returns:
        Path to the saved file.
    """
    _ensure_save_dir()
    save_path = SAVE_DIR / f"{slot}.json"
    data = state.model_dump_json(indent=2)
    save_path.write_text(data, encoding="utf-8")
    return save_path


def load_game(slot: str = "save1") -> GameState | None:
    """Load game state from a JSON file.

    Args:
        slot: Save slot name.

    Returns:
        Loaded game state, or None if save doesn't exist.
    """
    save_path = SAVE_DIR / f"{slot}.json"
    if not save_path.exists():
        return None

    data = save_path.read_text(encoding="utf-8")
    return GameState.model_validate_json(data)


def list_saves() -> list[dict[str, str]]:
    """List available save files with metadata.

    Returns:
        List of dicts with 'slot', 'team', 'province', 'season', 'modified'.
    """
    _ensure_save_dir()
    saves = []
    for save_file in sorted(SAVE_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            data = json.loads(save_file.read_text(encoding="utf-8"))
            config = data.get("config", {})
            season = data.get("season", {})

            # Extract human team name
            human_id = data.get("human_team_id")
            teams = data.get("teams", {})
            team_name = "?"
            if human_id and str(human_id) in teams:
                team_name = teams[str(human_id)].get("name", "?")

            # Format modification date
            mtime = save_file.stat().st_mtime
            modified = datetime.fromtimestamp(mtime).strftime("%d/%m/%Y %H:%M")

            saves.append({
                "slot": save_file.stem,
                "team": team_name,
                "province": config.get("province", "?"),
                "season": season.get("year", "?"),
                "modified": modified,
            })
        except (json.JSONDecodeError, KeyError, OSError):
            saves.append({
                "slot": save_file.stem,
                "team": "?",
                "province": "?",
                "season": "?",
                "modified": "?",
            })
    return saves


def delete_save(slot: str) -> bool:
    """Delete a save file.

    Returns:
        True if deleted, False if not found.
    """
    save_path = SAVE_DIR / f"{slot}.json"
    if save_path.exists():
        save_path.unlink()
        return True
    return False
