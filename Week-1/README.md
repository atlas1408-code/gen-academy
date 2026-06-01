# Week 1: PokeArena Analytics

A React SPA that integrates real-time Pokémon data from the PokeAPI v2, provides matchup comparisons via stat radar charts, and runs a calculated turn-based battle simulation.

## Features

- **Single Search** — Search any Pokémon by name, view official artwork, type badges, base stat bars, and a filterable moves grid
- **Battle Arena** — Pick two Pokémon (via search, quick-pick pills, or random type-based draft), compare stats on an overlay radar chart, and run a full battle simulation
- **Battle Simulation** — Turn-based engine with type effectiveness (dual-type stacking for 4x/0.25x), STAB, physical/special split, accuracy checks, and damage variance
- **Animated Playback** — Health bars drain in real-time, combat log scrolls per turn, winner overlay with data-driven analytical insight
- **Theme Toggle** — Switch between a premium dark-mode "Vibrant" theme and a monochrome "Blueprint" wireframe mode
- **Pokédex Device UI** — Full retro device shell with CRT scan-lines, pulsing LEDs, beveled buttons, and screen glow effects

## Tech Stack

- React 19 + Vite 6
- Tailwind CSS v4
- TanStack Query (react-query) — aggressive caching for PokeAPI
- Chart.js + react-chartjs-2 — radar chart
- Framer Motion — stat bar and health bar animations
- Docker (multi-stage: node build + nginx serve)

## Quick Start

### Local Development

```bash
cd Week-1
cp .env.sample .env
npm install
npm run dev
```

App runs at `http://localhost:5173`.

### Docker

Requires Docker Desktop — install it from [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/) (available for Mac, Windows, and Linux). Once installed, make sure Docker Desktop is running, then:

```bash
cd Week-1
cp .env.sample .env
docker compose up --build
```

App runs at `http://localhost:3000`.

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `VITE_POKEAPI_BASE_URL` | PokeAPI v2 base URL | `https://pokeapi.co/api/v2` |

## Architecture

```
src/
  api/pokeapi.js          — PokeAPI fetch functions
  hooks/usePokemon.js     — React Query hooks
  utils/typeEffectiveness.js — Type chart builder + multiplier calc
  utils/typeColors.js     — Type → color mapping
  engine/battleEngine.js  — Pure-function battle simulator
  pages/Explorer.jsx      — Single Search view
  pages/BattleArena.jsx   — Battle Arena view
  components/             — Reusable UI components
```
