# Ulaanbaatar signal network: simulation

The simulation service: a SUMO model of a Network of 15 Signal Sites on eight Corridors in central Ulaanbaatar, the Safety Guard, three Controllers, the live API the client uses, and Experiment Mode. The Python package is still named `corridor_sim`.

## Run

```sh
uv sync
uv run python -m corridor_sim.server          # http://localhost:8000
```

`HOST`, `PORT` and `CORS_ORIGINS` (comma-separated) change where it listens and which origins may call it.

Optional: copy `.env.example` to `.env.local` and set `OPENAI_API_KEY` to enable "Explain this decision". The narrator only describes a Signal Site's state after the fact; it never takes part in control (ADR 0002).

## Rebuild the network and Scenarios

The generated files in `data/` are committed, so this is only needed after changing `corridor_sim/build.py` or `corridor_sim/config.py`.

```sh
rm data/corridor.osm.xml   # only to re-download from OpenStreetMap
uv run python -m corridor_sim.build
```

The build:

1. Downloads the area from Overpass (`scripts/fetch_osm.sh`) if `data/corridor.osm.xml` is missing.
2. Runs `netconvert` with guessed sidewalks and crossings, leaving out OSM's separate footways.
3. Joins the nodes that `netconvert` left apart at six Signal Sites (`join_nodes` in `config.py`), and discards OSM turn lanes at four of them (`reset_connections`).
4. Adds the Crosswalk of the Mid-block Crossing at the State Department Store. The result is `data/corridor.net.xml`.
5. Resolves each of the 15 Signal Sites to the closest traffic light, at most 60 m away, with its Approaches, Crosswalks and Neighbours (`data/sites.json`). Neighbours come from the road graph: a drivable path, in either direction, of at most 700 m with no other controlled site on it.
6. Checks the sites and Corridors, and exits with a message and a non-zero status if a site has no Phase or more than three, an Approach, Crosswalk or vehicle signal no Phase serves, or a traffic light another site uses, or if two sites next to each other on a Corridor are not Neighbours.
7. Exports map geometry, sites and Corridors for the client (`data/network.json`).
8. Writes the five Scenarios (`data/scenarios/`). A vehicle volume is set per street class (arterial, collector, minor) and direction for every road entering the area. An incident that does not match exactly one Approach stops the build.

Each experiment result and the RL model record the SHA-256 of `data/corridor.net.xml`. If a rebuild changes the network, retrain RL and rerun the experiments; the server logs a warning when the model does not match.

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

`train` scores each candidate on two half-hour runs per iteration, so the command above simulates 336 runs. Each candidate runs inside the Safety Guard, so the policy learns within the caps rather than learning them. Training overwrites `data/models/rl-linear.json`. It uses the same five Scenarios with different random seeds from the evaluation, so the results show what the policy can learn on this Network, not how it generalises to unseen traffic.

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/network` | Geometry and bounds, Signal Sites with Approaches (with `direction` and `streetEn`), Crosswalks (with `streets`), Phases and Neighbours, `corridors` (`id`, names, `axis` `ew` or `ns`, `sites` in order), Scenarios, Controllers |
| GET | `/api/health` | Liveness and Scenario time |
| GET | `/api/state` | Scenario, Controller, speed, pause, caps |
| WS | `/ws` | `state` messages and live `frame` messages (signals, queues, waits, Congestion Levels, metrics, events, vehicles, pedestrians). `metrics.maxVehicleWait` is the Longest Approach wait. The first frame after connecting carries recent events |
| POST | `/api/control` | `pause`, `resume`, `speed`, `scenario`, `restart`, `controller`, `caps`, `button` (Pedestrian Demand), `block` (toggle a lane closure) |
| POST | `/api/explain` | Plain-language explanation of one Signal Site, `language` `en` or `mn` |
| GET/POST | `/api/experiments` | Read results (with `maxVehicleWait` per Controller) or start a background run of an hour per Scenario |

## Layout

- `corridor_sim/config.py`: Signal Site and Corridor definitions, default caps, timings and thresholds.
- `corridor_sim/build.py`: the network, Neighbour and Scenario build.
- `corridor_sim/model.py`: Signal Sites, links and Phases, read from the SUMO network, and site validation.
- `corridor_sim/phases.py`: builds compact conflict-free Phases where SUMO's guess has too many.
- `corridor_sim/sensing.py`: queues, Spillback, waiting pedestrians at both kerbs and Congestion Levels.
- `corridor_sim/guard.py`: the Safety Guard, covering clearance, yellow, all-red, min green, the caps and Overrides.
- `corridor_sim/controllers/`: the fixed-time, max-pressure and RL Controllers.
- `corridor_sim/engine.py`: the simulation loop, wait tracking, metrics, incidents and frames.
- `corridor_sim/server.py`: the FastAPI app.
- `corridor_sim/experiment.py`: Experiment Mode.
- `corridor_sim/explain.py`: the OpenAI narrator.
