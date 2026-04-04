# Volley

EVE Online damage calculator plugin for [SeAT](https://github.com/eveseat/seat) 5.x.

Uses real character skill data from SeAT's ESI integration to calculate accurate DPS and damage application, displayed as a DPS vs. Distance graph.

## Components

| Directory | Description |
|-----------|-------------|
| `engine/` | Python FastAPI microservice — Dogma calculation + Pyfa-style damage application formulas |
| `seat-plugin/` | SeAT Laravel plugin — UI, skill data integration, Chart.js graph |

## Architecture

```
SeAT (Laravel)  ──HTTP──▶  volley-engine (FastAPI)
  └ ESI skills                └ EVE SDE (Fuzzwork SQLite)
  └ EFT paste                 └ Dogma engine
  └ Chart.js graph            └ Damage application formulas
```

`volley-engine` runs as a standalone Docker Compose service, independent of SeAT's containers.

## Setup

### volley-engine

```bash
cd engine
docker compose up -d
```

### seat-plugin

Add to SeAT's `override.json`:
```json
{
  "autoload": {
    "Volley\\SeatVolley\\": "packages/volley/seat-plugin/src/"
  },
  "providers": ["Volley\\SeatVolley\\VolleyServiceProvider"]
}
```

Add to SeAT's `.env`:
```
VOLLEY_ENGINE_URL=http://volley-engine:8000
```

## License

MIT
