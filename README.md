# Smart traffic lights for Peace Avenue, Ulaanbaatar

An open-source demo of AI traffic-signal control on a 1.3 km stretch of Peace Avenue (Энх тайваны өргөн чөлөө) in central Ulaanbaatar. It controls five Signal Sites, from the State Department Store to Baga Toiruu East, past the Central Post Office and Sükhbaatar Square. Vehicles and pedestrians are simulated on real road geometry from OpenStreetMap. Controllers decide which Phase goes green, and a Safety Guard makes sure nobody waits too long.

The words used here (Signal Site, Approach, Crosswalk, Phase, Spillback, Safety Guard and so on) are defined in [GLOSSARY.md](GLOSSARY.md). The big decisions are in [docs/adr](docs/adr).

## How it decides

- **The Controller proposes, the Safety Guard decides** ([ADR 0002](docs/adr/0002-controller-proposes-safety-guard-decides.md)). Three Controllers can be switched live:
  - **Fixed-time**: cycles Phases on a schedule, like most of the city today. This is the Baseline.
  - **Max-pressure**: gives green where waiting queues most exceed the room on the roads they drain into. It looks at its Neighbours' queues, so it won't feed a Signal Site that is already jammed.
  - **RL**: a phase scorer trained in the simulation.
- **Caps the Safety Guard enforces, whatever the Controller wants:**
  - Pedestrians never wait more than **90 s**.
  - A vehicle Approach waits at most **120 s**. The Guard may extend that while the Approach's exit has Spillback, but never past **180 s**.
  - Min green, pedestrian walk and clearance, yellow and all-red always run.
  - Every Override is logged with the rule that forced it.
- **Camera vision** (`vision/`) shows what a camera would feed the Controller: queued vehicles per Approach and waiting pedestrians per Crosswalk, measured on recorded street video. It is a showcase, and the simulation does not use it ([ADR 0001](docs/adr/0001-simulation-first-on-sumo.md)).

## Results

These come from Experiment Mode: each Scenario runs for one hour, with the same traffic for every Controller (`sim/data/experiments/`). Each cell reads fixed-time → max-pressure → RL.

| Scenario | Avg vehicle wait | Avg pedestrian wait | Max pedestrian wait | Spillback minutes |
|---|---|---|---|---|
| Morning rush | 50.5 → 50.6 → 28.0 s | 24.8 → 17.9 → 16.2 s | 73 → 71 → 80 s | 63.8 → 136.5 → 24.0 |
| Midday | 51.9 → 37.0 → 29.1 s | 26.9 → 19.6 → 15.9 s | 72 → 74 → 80 s | 60.4 → 38.5 → 37.1 |
| Evening rush | 56.8 → 35.4 → 27.9 s | 25.4 → 19.6 → 16.3 s | 74 → 78 → 75 s | 98.0 → 45.4 → 25.4 |
| Incident: lane blocked | 54.5 → 55.6 → 26.9 s | 27.3 → 19.8 → 16.5 s | 74 → 72 → 78 s | 83.3 → 130.6 → 24.9 |
| Pedestrian surge | 47.8 → 46.1 → 29.8 s | 19.0 → 18.6 → 15.6 s | 73 → 79 → 80 s | 29.5 → 68.2 → 35.2 |

- **RL** roughly halves the average vehicle wait against the Baseline, and cuts the average pedestrian wait by about a third.
- **Max-pressure** clearly helps at midday and in the evening rush. In the morning rush and the incident it ties the Baseline on vehicle wait and builds more Spillback.
- **The pedestrian cap held**: no run let a pedestrian wait more than 90 s.

Traffic demand is generated, not measured, so compare the Controllers with each other, not with real Peace Avenue.

## Run it

Requirements: Python 3.12 with [uv](https://docs.astral.sh/uv/), Node 20+ with pnpm, or Docker.

```sh
# Simulation API on :8000
cd sim && uv sync && uv run python -m corridor_sim.server

# Vision API on :8001 (optional)
cd vision && uv sync && ./scripts/fetch_sample_videos.sh && uv run uvicorn app.main:app --port 8001

# Client on :5173
cd client && pnpm install && pnpm dev
```

With Docker, `docker compose up --build` starts all three (if your default buildx builder fails, run `docker buildx use desktop-linux` first); the client is then on http://localhost:8080. For the "Explain this decision" narrator, put `OPENAI_API_KEY=...` in `sim/.env.local`. Compose reads it if it exists.

## Repository

| Path | What |
|---|---|
| `sim/` | SUMO corridor model, Safety Guard, Controllers, live API, Experiment Mode, RL training. See [sim/README.md](sim/README.md) |
| `vision/` | YOLO vehicle and pedestrian counting on recorded video. See [vision/README.md](vision/README.md) |
| `client/` | React + Vite web client: live map, Signal Site detail, Operator controls, experiments, vision. See [client/README.md](client/README.md) |
| `docs/` | ADRs and research notes |

## Data and licences

- **Road network:** © OpenStreetMap contributors, available under the [ODbL](https://www.openstreetmap.org/copyright). The extract is `sim/data/corridor.osm.xml`.
- **Sample street videos:** from Wikimedia Commons. Credits and licences are in [vision/videos/SOURCES.md](vision/videos/SOURCES.md).
- **This project:** [AGPL-3.0](LICENSE), because the vision service uses Ultralytics YOLO ([ADR 0003](docs/adr/0003-agpl-open-source.md)).
