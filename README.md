# Calcio Manager

A terminal-based football management simulation inspired by **Championship Manager 01/02**, set in the world of Italian amateur **7-a-side football (CSI)**.

Built with [Textual](https://textual.textualize.io/) for a rich TUI experience.

## Features

- **Team management** — manage your amateur squad, pick formations, handle player roles
- **Match simulation** — watch games unfold with real-time commentary (in Italian)
- **League system** — compete in a full CSI-style season with calendar, standings, and results
- **Player generation** — procedurally generated players with Italian names and realistic attributes
- **Weather system** — dynamic weather affecting match conditions
- **Save/Load** — persist your career across sessions

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recommended package manager)

## Getting Started

```bash
# Clone the repo
git clone <repo-url> && cd quito

# Install dependencies
uv sync

# Run the game
uv run calcio-manager
```

## Development

```bash
# Install dev dependencies
uv sync --all-groups

# Run linter
uv run ruff check src/ tests/

# Run type checker
uv run mypy --strict src/

# Run tests
uv run pytest
```

## Project Structure

```
src/calcio_manager/
├── models/        # Pydantic data models (player, team, match, season, ...)
├── engine/        # Game logic (match sim, player gen, calendar, weather, ...)
├── state/         # Game state management and save/load
├── data/          # Localized content (Italian names, commentary) and art assets
└── ui/
    ├── screens/   # Textual screens (main menu, game hub, live match, ...)
    ├── widgets/   # Reusable UI components
    └── styles/    # Textual CSS
```

## License

MIT
