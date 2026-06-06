# Calcio Manager

Calcio Manager è un gestionale calcistico desktop ispirato a **Championship Manager 01/02**, ambientato nel calcio amatoriale italiano **CSI a 7**.

Il progetto è ora una applicazione **Tauri 2 + React + Rust**:

- **Rust** contiene stato, dominio e logica di gioco.
- **React** gestisce solo interfaccia, navigazione e visualizzazione.
- **Tauri** collega UI desktop e backend locale.

## Funzionalità

- **Carriera territoriale** — scegli regione, provincia e comune italiano.
- **Nuova partita guidata** — nome squadra, colori sociali, stadio e seed opzionale.
- **Tornei multi-girone** — gruppi generati dinamicamente in base alla provincia.
- **Generazione squadre/giocatori** — rose procedurali con nomi italiani, ruoli e attributi.
- **Calendario CSI-style** — round robin andata/ritorno e giornate aggregate.
- **Simulazione partita in Rust** — eventi, statistiche, rinunce, rigori dopo pareggio.
- **Live match React** — replay degli eventi generati dal backend.
- **Classifiche** — punti, differenza reti, disciplina e criteri head-to-head.
- **Transizione stagione** — al termine del calendario viene generata la stagione successiva.
- **Salvataggi versionati** — save/load/delete/list con metadata e compatibilità legacy.
- **Risorse dati migrate** — comuni italiani, nomi, commentary e locale TOML in `src-tauri/resources/data`.

## Requisiti

- Node.js e npm
- Rust stable con Cargo
- Dipendenze di sistema richieste da Tauri 2 per il proprio OS

## Avvio sviluppo

```bash
# installa dipendenze root e frontend
npm install
npm --prefix frontend install

# avvia l'app desktop in sviluppo
npm run dev
```

## Comandi utili

```bash
# TypeScript check frontend
npm run check:frontend

# Build frontend
npm run build:frontend

# Rust check
npm run check:rust

# Test Rust
npm run test:rust

# Check completo frontend + Rust
npm run check

# Test/check principale
npm test

# Build desktop Tauri
npm run build
```

## Struttura progetto

```text
frontend/                 React + TypeScript + Vite
  src/
    api/                  wrapper comandi Tauri
    screens/              schermate UI
    components/           componenti riusabili
    styles/               CSS globale

src-tauri/                Tauri shell + backend Rust
  src/
    commands/             API invocate dal frontend
    domain/
      models/             entità serializzabili Serde
      engine/             simulazione, calendario, classifiche, generatori
      services/           casi d'uso applicativi
  resources/data/         comuni, nomi, commentary, locale
```

## Stato migrazione

La migrazione da Python/Textual a Tauri/React/Rust è completata per lo stack applicativo principale. Il codice Python legacy è stato rimosso dal repository.

Restano come lavoro futuro funzionalità evolutive non bloccanti:

- gestione tattiche/formazioni più profonda lato backend e UI;
- schermata impostazioni e localizzazione runtime completa;
- ulteriore polish grafico in stile CM 01/02 moderno;
- ampliamento continuo della copertura test Rust.

Vedi `MIGRATION_TAURI.md` per il dettaglio dell'audit e delle milestone completate.
