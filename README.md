# CSI Calcio Manager

CSI Calcio Manager is a desktop football management game inspired by **Championship Manager 01/02**, set in Italian amateur **CSI 7-a-side football**.

The project is built with **Tauri 2 + React + Rust**:

- **Rust** owns the game state, domain model, simulation engine, saves, and local data access.
- **React** handles the desktop UI, navigation, and presentation.
- **Tauri** bridges the local Rust backend with the frontend application.

## Features

- **Local amateur career** — choose an Italian region, province, and municipality.
- **Guided new game flow** — configure club name, colors, stadium, season, and optional seed.
- **Dynamic multi-group tournaments** — groups are generated from the selected province.
- **Procedural clubs and players** — Italian names, roles, attributes, and squad strength.
- **CSI-style calendar** — two-legged round robin schedules aggregated by matchday.
- **Rust match simulation** — events, stats, forfeits, and penalty shootouts after draws.
- **Live match UI** — CM-style textual live commentary with always-visible stats and tabbed match details.
- **League tables** — points, goal difference, discipline, and head-to-head criteria.
- **Season rollover** — a new season is generated when the calendar is completed.
- **Versioned saves** — save/load/delete/list with metadata and compatibility checks.
- **Internal SQLite data layer** — bundled geography data is seeded into an app-local SQLite database.

## Requirements

- Node.js and npm
- Rust stable with Cargo
- System dependencies required by Tauri 2 for your operating system

See the official Tauri prerequisites for platform-specific setup: <https://tauri.app/start/prerequisites/>

## Development

Install dependencies:

```bash
npm install
npm --prefix frontend install
```

Run the desktop app in development mode:

```bash
npm run dev
```

## Useful commands

```bash
# Frontend TypeScript check
npm run check:frontend

# Frontend production build
npm run build:frontend

# Rust check
npm run check:rust

# Rust tests
npm run test:rust

# Full check: frontend + Rust
npm run check

# Main test command
npm test

# Desktop production build
npm run build

# Rust formatting
npm run fmt:rust
```

## Project structure

```text
frontend/                 React + TypeScript + Vite frontend
  src/
    api/                  Tauri command wrappers
    components/           reusable UI components
    screens/              application screens
    styles/               global CSS

src-tauri/                Tauri shell + Rust backend
  src/
    commands/             APIs invoked by the frontend
    domain/
      models/             serializable Serde domain entities
      engine/             simulation, calendar, standings, generators
      services/           application use cases
  resources/data/         bundled data: municipalities, names, commentary, locale files
```

## Data and saves

- Geography data is bundled with the app and seeded into an internal SQLite database under the Tauri app data directory.
- Commentary templates and player-name resources are bundled in `src-tauri/resources/data`.
- Game saves are versioned and stored locally by the Rust backend.

## Current focus

The application is playable as a local desktop prototype. Future work includes deeper tactics and lineup management, a complete settings/localization screen, broader Rust test coverage, and continued UI polish inspired by classic football management games.
