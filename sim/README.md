# Corridor simulation

The simulation service: a SUMO model of five Signal Sites on Peace Avenue, the Safety Guard, three Controllers, the live API the client uses, and Experiment Mode.

## Run

```sh
uv sync
uv run python -m corridor_sim.server          # http://localhost:8000
```

Optional: copy `.env.example` to `.env.local` and set `OPENAI_API_KEY` to enable "Explain this decision". The narrator only describes a Signal Site's state after the fact; it never takes part in control (ADR 0002).

## Rebuild the network and Scenarios

The generated files in `data/` are committed, so this is only needed after changing `corridor_sim/build.py` or `corridor_sim/config.py`.

```sh
rm data/corridor.osm.xml   # only to re-download from OpenStreetMap
uv run python -m corridor_sim.build
```

The build:

1. Downloads the corridor from Overpass (`scripts/fetch_osm.sh`).
2. Runs `netconvert` with guessed sidewalks and crossings.
3. Joins the State Department Store mid-block signal nodes and adds its Crosswalk.
4. Merges the eight Central Post Office signal nodes into one junction.
5. Resolves each Signal Site to its traffic light (`data/sites.json`).
6. Exports map geometry for the client (`data/network.json`).
7. Writes the five Scenarios (`data/scenarios/`).

## Experiment Mode

```sh
uv run python -m corridor_sim.experiment                       # every Scenario × every Controller, 3600 s each
uv run python -m corridor_sim.experiment --scenarios midday --controllers fixed-time,rl --duration 1800
```

Results land in `data/experiments/<scenario>.json`. The client's Experiments page reads them, and can start a run through `POST /api/experiments`.

## Train the RL Controller

```sh
uv run python -m corridor_sim.controllers.rl train --iterations 12 --population 14 --duration 1800 --workers 6
```

The RL Controller scores each Phase with a linear function of nine features: pressure, upstream queue, Spillback on exits, waiting pedestrians, the oldest pedestrian and vehicle waits, stickiness and the age of the current Phase. It is trained by cross-entropy policy search, which optimises the weights directly for average vehicle wait plus half the average pedestrian wait, penalising teleports and vehicles stuck waiting to enter the network.

Each candidate runs inside the Safety Guard, so the policy learns within the caps rather than learning them. Training takes about 4 minutes on an M2 Pro. It uses the same five Scenarios with different random seeds from the evaluation, so the results show what the policy can learn on this corridor, not how it generalises to unseen traffic.

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/network` | Geometry, Signal Sites with Approaches, Crosswalks, Phases and Neighbours, Scenarios, Controllers |
| GET | `/api/state` | Scenario, Controller, speed, pause, caps |
| WS | `/ws` | `state` messages and live `frame` messages (signals, queues, waits, Congestion Levels, metrics, events, vehicles, pedestrians) |
| POST | `/api/control` | `pause`, `resume`, `speed`, `scenario`, `restart`, `controller`, `caps`, `button` (Pedestrian Demand), `block` (toggle a lane closure) |
| POST | `/api/explain` | Plain-language explanation of one Signal Site, `language` `en` or `mn` |
| GET/POST | `/api/experiments` | Read results or start a background run |

## Layout

- `corridor_sim/model.py`: Signal Sites, links and Phases, read from the SUMO network.
- `corridor_sim/phases.py`: builds compact conflict-free Phases where SUMO's guess has too many.
- `corridor_sim/sensing.py`: queues, Spillback, waiting pedestrians and Congestion Levels.
- `corridor_sim/guard.py`: the Safety Guard, covering clearance, yellow, all-red, min green, the caps and Overrides.
- `corridor_sim/controllers/`: the fixed-time, max-pressure and RL Controllers.
- `corridor_sim/engine.py`: the simulation loop, wait tracking, metrics, incidents and frames.
- `corridor_sim/server.py`: the FastAPI app.
- `corridor_sim/experiment.py`: Experiment Mode.
- `corridor_sim/explain.py`: the OpenAI narrator.
